using System;
using System.IO;
using System.Text;
using System.Drawing;
using System.Windows.Forms;
using System.Collections.Generic;
using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

sealed class SteamWindow:Form {
    readonly string support=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"support");
    ComboBox game=new ComboBox(),role=new ComboBox(),difficulty=new ComboBox(),hudScale=new ComboBox(),pingMode=new ComboBox();
    TextBox name=new TextBox(),own=new TextBox(),peerBox=new TextBox(),log=new TextBox();
    Button install=new Button(),connect=new Button(),play=new Button(),stop=new Button(),init=new Button();
    CheckBox windowed=new CheckBox(); Timer timer=new Timer();SteamProbe api; SteamTunnel tunnel;
    Process server; Stopwatch clock=new Stopwatch();ulong peer; bool busy;long nextStatus;
    JavaScriptSerializer json=new JavaScriptSerializer();
    TabControl tabs=new TabControl();
    CheckBox maxed=new CheckBox(),items=new CheckBox(),wasd=new CheckBox(),skip=new CheckBox();
    NumericUpDown seconds=new NumericUpDown();
    ComboBox mode=new ComboBox(),adapter=new ComboBox(); TextBox address=new TextBox();
    Button apply=new Button(),disable=new Button(),restore=new Button(),lanSetup=new Button(),lanCheck=new Button(),lanStop=new Button();
    string appliedTransport="Steam"; List<Dictionary<string,object>> networks=new List<Dictionary<string,object>>();
    class NetworkChoice {public string IP,Alias;public override string ToString(){return Alias+" - "+IP;}}
    public SteamWindow(){
        Text="Omerta Co-op v1.5 - HUD and pings";Size=new Size(860,850);MinimumSize=new Size(820,800);Font=new Font("Segoe UI",10);
        var main=new TableLayoutPanel{Dock=DockStyle.Fill,Padding=new Padding(16),ColumnCount=2,RowCount=7};main.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,145));main.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));Controls.Add(main);
        var intro=new Label{AutoSize=true,Text="OMERTA CO-OP  /  Steam first, LAN and VPN as fallback"};main.Controls.Add(intro,0,0);main.SetColumnSpan(intro,2);
        var folders=new FlowLayoutPanel{Dock=DockStyle.Fill,Height=36};game.Width=440;var browse=new Button{Text="Browse",AutoSize=true};folders.Controls.AddRange(new Control[]{game,browse});browse.Click+=(s,e)=>{using(var d=new FolderBrowserDialog()){if(d.ShowDialog()==DialogResult.OK)game.Text=d.SelectedPath;}};Row(main,1,"Game folder",folders);
        Row(main,2,"Player name",name);role.Items.AddRange(new object[]{"Host","Join"});role.DropDownStyle=ComboBoxStyle.DropDownList;role.SelectedIndex=0;Row(main,3,"Play as",role);
        tabs.Dock=DockStyle.Fill;tabs.Height=420;main.Controls.Add(tabs,0,4);main.SetColumnSpan(tabs,2);
        var st=Page("Steam (recommended)");var op=Page("Patches and options");var lan=Page("LAN / Radmin fallback");
        own.ReadOnly=true;Row(st,0,"Your Steam ID",own);Row(st,1,"Friend's Steam ID",peerBox);
        init.Text="Initialize Steam";install.Text="Install / update";connect.Text="Connect";stop.Text="Stop connection";
        Buttons(st,2,init,install,connect,stop);
        Note(st,3,"Exchange Steam IDs; choose opposite Host / Join roles.\nInstall with Omerta closed, then both click Connect.\nWait for Steam connection ready before Play. Keep this launcher open.");
        maxed.Text="Unlock characters + level 12 / default perks";items.Text="Unlock all available weapons";wasd.Text="WASD camera + arrow keys";skip.Text="Skip Kalypso launcher";
        foreach(var c in new[]{maxed,items,wasd,skip}){c.AutoSize=true;c.Checked=true;}
        Row(op,0,"Characters",maxed);Row(op,1,"Weapons",items);Row(op,2,"Camera",wasd);Row(op,3,"Game launch",skip);
        seconds.Maximum=3600;Row(op,4,"Round timer (sec)",seconds);Note(op,5,"0 = unlimited; 60 = original; 300 = five minutes. Both players use the same timer.");
        difficulty.Items.AddRange(new object[]{"Normal","Easy","Hard","Insane"});difficulty.DropDownStyle=ComboBoxStyle.DropDownList;difficulty.SelectedIndex=0;Row(op,6,"Host bot difficulty",difficulty);
        apply.Text="Apply selected patches";disable.Text="Disable optional patches";restore.Text="Restore original game";hudScale.Items.AddRange(new object[]{"Default (100%)","150% (1.5x)","200% (2x)","300% (3x)"});hudScale.DropDownStyle=ComboBoxStyle.DropDownList;hudScale.SelectedIndex=0;
        pingMode.Items.AddRange(new object[]{"Off","Middle mouse click","Alt + left click"});pingMode.DropDownStyle=ComboBoxStyle.DropDownList;pingMode.SelectedIndex=1;
        Row(op,7,"In-game HUD size",hudScale);Row(op,8,"Shared map ping",pingMode);
        Note(op,9,"HUD size is local; 2x/3x may overlap on smaller screens. Pings last five seconds.\nBoth players need v1.5 for shared pings. Combat maps only.");
        Buttons(op,10,apply,disable,restore);
        Note(op,11,"Close the game and stop the connection before applying. Turning off unlocks\nstops future grants; it does not remove saved levels or weapons. Restore removes\nthe co-op Lua patch too, but retains profiles and saves. HD textures are separate.");
        mode.Items.AddRange(new object[]{"Home LAN","Radmin / ZeroTier"});mode.DropDownStyle=ComboBoxStyle.DropDownList;mode.SelectedIndex=0;adapter.DropDownStyle=ComboBoxStyle.DropDownList;
        Row(lan,0,"Network",mode);Row(lan,1,"Host interface",adapter);Row(lan,2,"Host IP",address);
        lanSetup.Text="Apply LAN / VPN setup";lanCheck.Text="Test displayed IP";lanStop.Text="Stop fallback host";Buttons(lan,3,lanSetup,lanCheck,lanStop);
        Note(lan,4,"Host selects its interface; Join enters the host IP.\nHost setup starts the helper and configures its firewall rule (Windows approval).\nBoth players must already be on the same LAN or VPN network.\nThe options tab applies to both Steam and fallback connections.");
        var launch=new FlowLayoutPanel{Dock=DockStyle.Fill,Height=40};play.Text="Play";play.AutoSize=true;windowed.Text="Windowed 1920 x 1080";windowed.AutoSize=true;windowed.Checked=true;launch.Controls.AddRange(new Control[]{play,windowed});main.Controls.Add(launch,0,5);main.SetColumnSpan(launch,2);
        log.Multiline=true;log.ReadOnly=true;log.ScrollBars=ScrollBars.Vertical;log.Dock=DockStyle.Fill;main.Controls.Add(log,0,6);main.SetColumnSpan(log,2);
        for(int i=0;i<6;i++)main.RowStyles.Add(new RowStyle(SizeType.AutoSize));main.RowStyles.Add(new RowStyle(SizeType.Percent,100));
        init.Click+=(s,e)=>{try{api=new SteamProbe(game.Text,Write);own.Text=api.ID.ToString();timer.Start();RefreshButtons();}catch(Exception ex){Write(ex.Message);}};
        install.Click+=async(s,e)=>await Prepare();connect.Click+=async(s,e)=>await Connect();stop.Click+=(s,e)=>Stop();
        apply.Click+=async(s,e)=>await RunAction("options");
        disable.Click+=async(s,e)=>{maxed.Checked=items.Checked=wasd.Checked=skip.Checked=false;seconds.Value=60;difficulty.Text="Normal";hudScale.SelectedIndex=0;pingMode.SelectedIndex=0;await RunAction("options");};
        restore.Click+=async(s,e)=>await RunAction("restore_game");
        lanSetup.Click+=async(s,e)=>await RunAction("fallback_setup");lanCheck.Click+=async(s,e)=>await RunAction("fallback_check");lanStop.Click+=async(s,e)=>await RunAction("fallback_stop");
        play.Click+=async(s,e)=>await RunAction("play");
        role.SelectedIndexChanged+=(s,e)=>{RefreshButtons();SelectAddress();};mode.SelectedIndexChanged+=(s,e)=>FillNetworks("");adapter.SelectedIndexChanged+=(s,e)=>SelectAddress();tabs.SelectedIndexChanged+=(s,e)=>RefreshButtons();
        timer.Interval=16;timer.Tick+=(s,e)=>Tick();Shown+=async(s,e)=>await LoadSettings();
        FormClosing+=(s,e)=>{if(busy){e.Cancel=true;Write("Wait for the current setup operation to finish.");}};
        FormClosed+=(s,e)=>{timer.Stop();Stop();if(api!=null)api.Dispose();};RefreshButtons();
    }
    TableLayoutPanel Page(string title){var page=new TabPage(title){Padding=new Padding(10),AutoScroll=true};tabs.TabPages.Add(page);var table=new TableLayoutPanel{Dock=DockStyle.Top,AutoSize=true,ColumnCount=2};table.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,150));table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));page.Controls.Add(table);return table;}
    static void Note(TableLayoutPanel p,int row,string text){var label=new Label{Text=text,AutoSize=true,Margin=new Padding(3,8,3,8)};p.Controls.Add(label,0,row);p.SetColumnSpan(label,2);}
    static void Buttons(TableLayoutPanel p,int row,params Button[] buttons){var line=new FlowLayoutPanel{Dock=DockStyle.Fill,AutoSize=true};foreach(var b in buttons){b.AutoSize=true;line.Controls.Add(b);}p.Controls.Add(line,0,row);p.SetColumnSpan(line,2);}
    void SelectAddress(){if(role.Text=="Host"&&adapter.SelectedItem is NetworkChoice)address.Text=((NetworkChoice)adapter.SelectedItem).IP;}
    void FillNetworks(string selected){adapter.Items.Clear();foreach(var n in networks){string alias=(string)n["InterfaceAlias"];bool vpn=alias.ToLowerInvariant().Contains("radmin")||alias.ToLowerInvariant().Contains("zerotier")||alias.ToLowerInvariant().Contains("tailscale");if(vpn!=(mode.SelectedIndex==1))continue;if(!vpn&&(alias.ToLowerInvariant().Contains("vethernet")||alias.ToLowerInvariant().Contains("vmware")||alias.ToLowerInvariant().Contains("virtual")))continue;adapter.Items.Add(new NetworkChoice{IP=(string)n["IPAddress"],Alias=alias});}if(adapter.Items.Count>0)adapter.SelectedIndex=0;for(int i=0;i<adapter.Items.Count;i++)if(((NetworkChoice)adapter.Items[i]).IP==selected)adapter.SelectedIndex=i;}
    async Task RunAction(string action){busy=true;RefreshButtons();try{Write(await Backend(action));if(action=="fallback_setup")appliedTransport="Fallback";if(action=="restore_game")appliedTransport="None";}catch(Exception ex){Write(ex.Message);}finally{busy=false;RefreshButtons();}}
    internal void ShowPage(int page){tabs.SelectedIndex=page;}
    internal bool Busy {get{return busy;}}
    static void Row(TableLayoutPanel p,int row,string label,Control c){p.Controls.Add(new Label{Text=label,AutoSize=true},0,row);c.Dock=DockStyle.Fill;p.Controls.Add(c,1,row);}
    void Write(string s){if(IsDisposed)return;string line=DateTime.Now.ToString("HH:mm:ss")+" "+s;log.AppendText(line+Environment.NewLine);File.AppendAllText(Path.Combine(support,"steam-bridge.log"),line+Environment.NewLine);}
    void RefreshButtons(){bool active=tunnel!=null;bool editable=!active&&!busy;init.Enabled=api==null&&!busy;install.Enabled=editable;connect.Enabled=api!=null&&editable;stop.Enabled=active&&!busy;play.Enabled=!busy&&((active&&tunnel.Ready)||(appliedTransport=="Fallback"&&tabs.SelectedIndex==2));game.Enabled=api==null&&!busy;role.Enabled=editable;peerBox.ReadOnly=!editable;name.ReadOnly=!editable;difficulty.Enabled=editable&&role.Text=="Host";foreach(var c in new Control[]{maxed,items,wasd,skip,seconds,hudScale,pingMode,apply,disable,restore,lanSetup,mode,adapter})c.Enabled=editable;mode.Enabled=adapter.Enabled=editable&&role.Text=="Host";address.ReadOnly=!editable||role.Text=="Host";lanCheck.Enabled=!busy&&!active;lanStop.Enabled=!busy&&!active;}
    Dictionary<string,object> Request(string action){return new Dictionary<string,object>{{"action",action},{"game",game.Text},{"name",name.Text},{"role",role.Text},{"peer",peerBox.Text.Trim()},{"difficulty",difficulty.Text.ToLowerInvariant()},{"windowed",windowed.Checked},{"skip_launcher",skip.Checked},{"mode",mode.SelectedIndex==0?"LAN":"VPN"},{"address",address.Text},{"interface",adapter.SelectedItem is NetworkChoice?((NetworkChoice)adapter.SelectedItem).Alias:""},{"options",new Dictionary<string,object>{{"maxed",maxed.Checked?"1":"0"},{"items",items.Checked?"1":"0"},{"wasd",wasd.Checked?"1":"0"},{"turn_seconds",seconds.Value.ToString()},{"hud_scale",new[]{"100","150","200","300"}[Math.Max(0,hudScale.SelectedIndex)]},{"ping",new[]{"off","middle","alt_left"}[Math.Max(0,pingMode.SelectedIndex)]}}}};}
    async Task<Dictionary<string,object>> Call(Dictionary<string,object> q){string input=json.Serialize(q);return await Task.Run(()=>{
        var p=new Process{StartInfo=new ProcessStartInfo(Path.Combine(support,"runtime/OmertaCoopServer.exe"),"\""+Path.Combine(support,"steam_setup.py")+"\""){UseShellExecute=false,CreateNoWindow=true,RedirectStandardInput=true,RedirectStandardOutput=true,RedirectStandardError=true}};
        p.Start();var err=p.StandardError.ReadToEndAsync();p.StandardInput.Write(input);p.StandardInput.Close();string output=p.StandardOutput.ReadToEnd();p.WaitForExit();string error=err.Result;p.Dispose();
        Dictionary<string,object> r;try{r=json.Deserialize<Dictionary<string,object>>(output);}catch{throw new Exception(error+output);}if(!(bool)r["ok"])throw new Exception((string)r["error"]);return (Dictionary<string,object>)r["data"];
    });}
    async Task<string> Backend(string action){return (string)(await Call(Request(action)))["message"];}
    async Task LoadSettings(){busy=true;RefreshButtons();try{var r=await Call(new Dictionary<string,object>{{"action","status"}});foreach(object g in (System.Collections.IEnumerable)r["games"])game.Items.Add(g);game.Text=(string)r["game"];name.Text=(string)r["name"];role.Text=(string)r["role"];peerBox.Text=(string)r["peer"];difficulty.Text=System.Globalization.CultureInfo.InvariantCulture.TextInfo.ToTitleCase((string)r["difficulty"]);var opts=(Dictionary<string,object>)r["options"];maxed.Checked=(string)opts["maxed"]=="1";items.Checked=(string)opts["items"]=="1";wasd.Checked=(string)opts["wasd"]=="1";seconds.Value=Math.Max(0,Math.Min(3600,decimal.Parse((string)opts["turn_seconds"])));hudScale.SelectedIndex=Math.Max(0,Array.IndexOf(new[]{"100","150","200","300"},(string)opts["hud_scale"]));pingMode.SelectedIndex=Math.Max(0,Array.IndexOf(new[]{"off","middle","alt_left"},(string)opts["ping"]));skip.Checked=(bool)r["skip_launcher"];appliedTransport=(string)r["transport"];foreach(object n in (System.Collections.IEnumerable)r["adapters"])networks.Add((Dictionary<string,object>)n);var host=(Dictionary<string,object>)r["host"];mode.SelectedIndex=host.ContainsKey("mode")&&(string)host["mode"]=="VPN"?1:0;FillNetworks(host.ContainsKey("host")?(string)host["host"]:"");if(role.Text=="Join")address.Text=(string)r["client_host"];}catch(Exception ex){Write(ex.Message);}finally{busy=false;RefreshButtons();}}
    async Task Prepare(){busy=true;RefreshButtons();try{Write(await Backend("prepare"));appliedTransport="Steam";}catch(Exception ex){Write(ex.Message);}finally{busy=false;RefreshButtons();}}
    async Task Connect(){
        if(!ulong.TryParse(peerBox.Text,out peer)||peer==api.ID||(peer>>56)!=1||((peer>>52)&15)!=1||(uint)peer==0){Write("Enter your friend's numeric Steam ID, not your own.");return;}
        busy=true;RefreshButtons();try{
            Write(await Backend("prepare"));appliedTransport="Steam"; // Revalidate role/port and preserve profile before every run.
            if(role.Text=="Host"){
                var probe=new TcpListener(IPAddress.Loopback,50670);probe.Start();probe.Stop();
                server=new Process{StartInfo=new ProcessStartInfo(Path.Combine(support,"runtime/OmertaCoopServer.exe"),"-u \""+Path.Combine(support,"server.py")+"\" --bind 127.0.0.1 --port 50670"){UseShellExecute=false,CreateNoWindow=true,WorkingDirectory=support,RedirectStandardOutput=true,RedirectStandardError=true}};
                server.OutputDataReceived+=(s,e)=>SaveServerLog(e.Data);server.ErrorDataReceived+=(s,e)=>SaveServerLog(e.Data);server.Start();server.BeginOutputReadLine();server.BeginErrorReadLine();
                bool ready=false;for(int i=0;i<40;i++){if(server.HasExited)throw new Exception("Host helper exited. See support/steam-server.log.");try{using(var c=new TcpClient()){await c.ConnectAsync(IPAddress.Loopback,50670);}ready=true;break;}catch(SocketException){}await Task.Delay(100);}
                if(!ready)throw new Exception("Host helper startup timed out.");Write("Host helper ready on local loopback only.");
            }
            tunnel=new SteamTunnel(new SteamPeer(api,peer),role.Text=="Host",50670,50671,Write);clock.Restart();nextStatus=0;Write("Connecting through Steam. Initial relay setup may take 20-60 seconds.");
        }catch(Exception ex){Write(ex.Message);Stop();}finally{busy=false;RefreshButtons();}
    }
    void SaveServerLog(string line){if(line!=null)lock(support){File.AppendAllText(Path.Combine(support,"steam-server.log"),line+Environment.NewLine);}}
    void Tick(){try{if(tunnel==null){if(api!=null)api.Pump();return;}if(server!=null&&server.HasExited)throw new Exception("Host helper stopped.");tunnel.Tick(clock.ElapsedMilliseconds);if(clock.ElapsedMilliseconds>=nextStatus){nextStatus=clock.ElapsedMilliseconds+5000;Write(api.Status(peer)+" Sent="+tunnel.SentBytes+" Received="+tunnel.ReceivedBytes);}RefreshButtons();}catch(Exception ex){Write(ex.Message);Stop();}}
    void Stop(){if(tunnel!=null){tunnel.Dispose();tunnel=null;}if(server!=null){try{if(!server.HasExited){server.Kill();server.WaitForExit();}}finally{server.Dispose();server=null;}}RefreshButtons();}
}
