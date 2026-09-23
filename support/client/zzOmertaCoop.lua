-- Experimental, opt-in private connection. Original gameplay serialization stays intact.
-- Loaded from the user's own rebuilt Lua.hpk; no original game code is distributed.
local settings = {host = "127.0.0.1", port = 50669, token = "", profile = "", name = "Player", smoke = "0", maxed = "1", turn_seconds = "0", wasd = "1"}
local install_dir = "" -- OMERTA_INSTALL_DIR
local function diagnostic(message)
  DebugPrint(message .. "\n")
  local file = io.open(install_dir .. "OmertaCoop-diagnostic.log", "a")
  if file then file:write(message .. "\n"); file:close() end
end
local settings_file = io.open(install_dir .. "OmertaCoop.ini", "r")
if settings_file then
  for line in settings_file:lines() do
    local key, value = string.match(line, "^([%w_]+)=(.-)%s*$")
    if key and settings[key] ~= nil then
      settings[key] = key == "port" and tonumber(value) or value
    end
  end
  settings_file:close()
end
config.host = settings.host
config.cloud_port = settings.port
local turn_seconds = tonumber(settings.turn_seconds) or 0
if turn_seconds < 0 or turn_seconds > 3600 then turn_seconds = 0 end
if config.MPTurnTimer and turn_seconds > 0 then config.MPTurnTimer.time = turn_seconds * 1000 end
local maximum = 8388608

local function uint32(n)
  return string.char(((n - n % 16777216) / 16777216) % 256,
    ((n - n % 65536) / 65536) % 256, ((n - n % 256) / 256) % 256, n % 256)
end

local function encode(v, depth)
  depth = depth or 0
  if depth > 24 then error("Coop nesting limit") end
  local t = type(v)
  if t == "nil" then return "z" end
  if t == "boolean" then return v and "t" or "f" end
  if t == "string" or t == "number" then
    local data = t == "number" and tostring(v) or v
    if #data > maximum then error("Coop value too large") end
    return (t == "number" and "n" or "s") .. uint32(#data) .. data
  end
  if t == "table" then
    local parts, count = {}, 0
    for key, value in pairs(v) do
      count = count + 1
      if count > 20000 then error("Coop table too large") end
      parts[#parts + 1] = encode(key, depth + 1)
      parts[#parts + 1] = encode(value, depth + 1)
    end
    return "m" .. uint32(count) .. table.concat(parts)
  end
  error("Unsupported private RPC value: " .. t)
end

local function decode(data)
  local pos, budget = 1, 40000
  local function take(n)
    if n < 0 or pos + n - 1 > #data then error("Truncated private RPC") end
    local s = string.sub(data, pos, pos + n - 1)
    pos = pos + n
    return s
  end
  local function read_uint()
    local a,b,c,d = string.byte(take(4), 1, 4)
    if a > 0 then error("Private RPC length limit") end
    return b * 65536 + c * 256 + d
  end
  local read_value
  read_value = function(depth)
    budget = budget - 1
    if depth > 24 or budget < 0 then error("Private RPC complexity limit") end
    local tag = take(1)
    if tag == "z" then return nil end
    if tag == "f" then return false end
    if tag == "t" then return true end
    if tag == "s" or tag == "n" then
      local n = read_uint()
      if n > maximum or (tag == "n" and n > 12) then error("Private RPC value limit") end
      local value = take(n)
      if tag == "n" then
        local number = tonumber(value)
        if not number then error("Invalid private RPC number") end
        return number
      end
      return value
    end
    if tag == "m" then
      local n = read_uint()
      if n > 20000 then error("Private RPC table limit") end
      local result = {}
      for i = 1, n do
        local key = read_value(depth + 1)
        if type(key) ~= "string" and type(key) ~= "number" then error("Invalid private RPC key") end
        if result[key] ~= nil then error("Duplicate private RPC key") end
        result[key] = read_value(depth + 1)
      end
      return result
    end
    error("Unknown private RPC tag")
  end
  local result = read_value(0)
  if pos ~= #data + 1 then error("Private RPC trailing data") end
  return result
end

function NetCloudSocket:Rpc(name, ...)
  local packet = {name, ...}
  packet.n = select("#", ...) + 1
  local body = encode(packet)
  if #body > maximum then error("Private RPC frame limit") end
  BaseSocket.Send(self, uint32(#body) .. body)
end

function NetCloudSocket:OnReceive()
  while #self.receive_buffer >= 4 do
    local a,b,c,d = string.byte(self.receive_buffer, 1, 4)
    if a ~= 0 then self:Disconnect(); return end
    local size = b * 65536 + c * 256 + d
    if size < 1 or size > maximum then self:Disconnect(); return end
    if #self.receive_buffer < size + 4 then return end
    local body = string.sub(self.receive_buffer, 5, size + 4)
    self.receive_buffer = string.sub(self.receive_buffer, size + 5)
    local ok, err = pcall(function()
      local packet = decode(body)
      if type(packet) ~= "table" or type(packet.n) ~= "number" or packet.n < 1 or packet.n > 32 then
        error("Invalid private RPC envelope")
      end
      local name = packet[1]
      -- Deliberately exclude generic evaluation and server-to-client RFC requests.
      local allowed = {
        rpcRfcResult=true, rpcChallengeAccepted=true, rpcSyncPlayersData=true,
        rpcStartGame=true, rpcChangeLoadingStatus=true, rpcMissingMission=true,
        rpcEvent=true, rpcDropped=true, rpcDesync=true, rpcSetPause=true,
        rpcChatMsg=true, rpcChatSysMsg=true, rpcCoopVictoryConfirmed=true
      }
      if not allowed[name] then error("Unexpected private RPC") end
      self:CallRpc(unpack(packet, 1, packet.n))
    end)
    if not ok then
      diagnostic("OMERTA_COOP_RPC_ERROR " .. tostring(err))
      self:Disconnect()
      return
    end
  end
end

function NetCloudSocket:WaitConnect(timeout, host, port, auto_register)
  diagnostic("OMERTA_COOP_CONNECT_BEGIN")
  if #settings.profile < 8 then
    diagnostic("OMERTA_COOP_CONFIG_ERROR: run configure.py for this PC first")
    return "param"
  end
  self.login_state = "connecting"
  local err = MessageSocket.WaitConnect(self, timeout, settings.host, settings.port)
  diagnostic("OMERTA_COOP_TCP " .. tostring(err or "ok"))
  if err then return err end
  local hello_err, id = self:Rfc("rpcCoopHello", settings.token, settings.profile, settings.name, NetworkVersion)
  if hello_err then self:Disconnect(); return hello_err end
  self.account_id = id
  self.login_state = "logged"
  diagnostic("OMERTA_COOP_CONNECTED " .. tostring(id))
end

-- Only this opt-in connection uses plaintext payloads over its private TCP channel.
function NetCloudSocket:Encrypt(value) return value end
function NetCloudSocket:Decrypt(value) return value end

function NetUpdate(to_add, to_remove, to_ignore, to_reject, to_challenge)
  if not netCloudSocket then return "disconnected" end
  return netCloudSocket:Rfc("rpcCoopUpdate", to_challenge or {}, to_reject or {})
end

function NetSetVictory(victory, is_coop, id_to_gain)
  if not netCloudSocket then return "disconnected" end
  return netCloudSocket:Rfc("rpcCoopVictory", victory and true or false, is_coop and true or false, id_to_gain)
end

function NetCloudSocket:rpcCoopVictoryConfirmed(victory, gain)
  Msg("VictoryConfirmed", {victory = victory, gain = gain})
end

-- Private multiplayer progression option; the campaign loader is unchanged.
local original_load_multiplayer = LoadMultiplayerStorage
function LoadMultiplayerStorage(...)
  original_load_multiplayer(...)
  if settings.maxed ~= "1" or not SessionStorage.Multiplayer then return end
  UnlockAllMembers()
  local gang = SessionStorage.UICity.gang
  local visited = {}
  local function maximize(list)
    for i = 1, #list do
      local member = list[i]
      if not visited[member] then
        visited[member] = true
        member.mp_max_level = 12
        -- Rebuild the character's own default progression even when an older
        -- private profile already says level 12 but lacks its level-up perks.
        local definition = DataInstances.CombatUnitDef[member.name]
        if definition then
          for slot = 1, 11 do member["perk" .. slot] = definition["perk" .. slot] or "" end
        end
        ResetHenchman(member)
        LevelUpPerks(member, 12)
        member:Recalc()
        if member.Level ~= 12 then
          diagnostic("OMERTA_COOP_PERK_CHECK " .. tostring(member.name) .. " level=" .. tostring(member.Level))
        end
      end
    end
  end
  maximize(gang.Unlocked)
  maximize(gang.Hired)
  gang.MPUnlockedWeapons = gang.MPUnlockedWeapons or {}
  local weapons = GetAllWeaponTypes()
  for i = 1, #weapons do table_insert_unique(gang.MPUnlockedWeapons, weapons[i]) end
  diagnostic("OMERTA_COOP_MAXED characters=" .. #gang.Unlocked .. " weapons=" .. #gang.MPUnlockedWeapons)
end

diagnostic("OMERTA_COOP_PROTOTYPE_LOADED " .. tostring(settings.host) .. ":" .. tostring(settings.port))
diagnostic("OMERTA_COOP_CONFIG readable=" .. tostring(settings_file ~= nil) .. " valid=" .. tostring(#settings.profile >= 8) .. " smoke=" .. settings.smoke)

local original_connect = NetConnect
function NetConnect(...)
  diagnostic("OMERTA_COOP_NETCONNECT")
  local err = original_connect(...)
  diagnostic("OMERTA_COOP_NETCONNECT_RESULT " .. tostring(err or "ok"))
  return err
end

function OnMsg.ClassesBuilt()
  diagnostic("OMERTA_COOP_CLASSES_BUILT")
  local function camera_input_active(dialog)
    return settings.wasd == "1" and GetKeyboardFocus() == dialog and not IsCameraLocked()
      and cameraRTS.IsActive() and not terminal.IsKeyPressed(const.vkControl)
      and not terminal.IsKeyPressed(const.vkAlt)
  end
  local function add_controls(class, combat)
    local original_init = class.Init
    local original_keydown = class.OnKbdKeyDown
    function class:Init(...)
      original_init(self, ...)
      if combat and GameState.multiplayer and turn_seconds == 0 then self:StopTimer() end
      if settings.wasd ~= "1" then return end
      self:CreateThread("omerta_wasd_camera", function()
        local previous = RealTime()
        while true do
          Sleep(16)
          local now = RealTime()
          local elapsed = Min(now - previous, 50)
          previous = now
          if camera_input_active(self) then
            local right = (terminal.IsKeyPressed(const.vkD) and 1 or 0) - (terminal.IsKeyPressed(const.vkA) and 1 or 0)
            local forward = (terminal.IsKeyPressed(const.vkW) and 1 or 0) - (terminal.IsKeyPressed(const.vkS) and 1 or 0)
            if right ~= 0 or forward ~= 0 then
              local eye, look = cameraRTS.GetPosLookAt()
              local direction = (look - eye):SetZ(0)
              if direction:Len2D() > 0 then
                direction = SetLen(direction, 4096)
                direction = direction * forward + point(direction:y(), -direction:x(), 0) * right
                local speed = terminal.IsKeyPressed(const.vkShift) and hr.RTSCamera.MoveSpeedFast or hr.RTSCamera.MoveSpeedNormal
                local distance = MulDivRound(speed * terrain.GameUnitsInMeter(), elapsed, 1000)
                local target = cameraRTS.ClampLookat(look + SetLen(direction, distance)):SetZ(look:z())
                cameraRTS.SetCameraPrecise(eye + target - look, target, 0)
              end
            end
          end
        end
      end)
    end
    function class:OnKbdKeyDown(char, key, repeated)
      if camera_input_active(self) and (key == const.vkW or key == const.vkA or key == const.vkS or key == const.vkD) then
        return "break"
      end
      return original_keydown(self, char, key, repeated)
    end
  end
  add_controls(CombatInterface, true)
  add_controls(DistrictInterface, false)
  diagnostic("OMERTA_COOP_CONTROLS timer=" .. turn_seconds .. " wasd=" .. settings.wasd)
end
function OnMsg.Start()
  diagnostic("OMERTA_COOP_START")
  local command = (GetAppCmdLine() or "") .. " "
  if string.find(command, "%-windowed%s") then
    local width = tonumber(string.match(command, "%-width%s+(%d+)%s")) or 1920
    local height = tonumber(string.match(command, "%-height%s+(%d+)%s")) or 1080
    if width < 800 or width > 7680 then width = 1920 end
    if height < 600 or height > 4320 then height = 1080 end
    CreateRealTimeThread(function()
      Sleep(1000)
      hr.ChangeVideoMode(width, height, 0, false, config.VSync == 1)
      diagnostic("OMERTA_COOP_WINDOWED " .. width .. "x" .. height)
    end)
  end
end

if settings.smoke == "1" and settings.host == "127.0.0.1" then
  function OnMsg.Start()
    CreateRealTimeThread(function()
      Sleep(3000)
      diagnostic("OMERTA_COOP_SMOKE_BEGIN")
      local connection = NetCloudSocket:new({})
      local err = connection:WaitConnect(10000, settings.host, settings.port)
      diagnostic("OMERTA_COOP_SMOKE_LOGIN " .. tostring(err or "ok"))
      if not err then
        local name_err, name = connection:Rfc("rpcGetName", NetworkVersion)
        diagnostic("OMERTA_COOP_SMOKE_NAME " .. tostring(name_err or "ok"))
        local rating_err, rating = connection:Rfc("rpcGetRating")
        diagnostic("OMERTA_COOP_SMOKE_RATING " .. tostring(rating_err or "ok"))
      end
      connection:Disconnect()
      diagnostic("OMERTA_COOP_SMOKE_END")
    end)
  end
end
