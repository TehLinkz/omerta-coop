using System;
using System.IO;
using System.Runtime.InteropServices;

// x86 ABI for Omerta's SteamUser016, SteamUtils005, SteamNetworking005.
// Interface order: Valve's public ISteamUser/ISteamUtils/ISteamNetworking headers.
sealed class SteamProbe : IDisposable {
    [DllImport("kernel32", CharSet=CharSet.Unicode, SetLastError=true)] static extern IntPtr LoadLibraryEx(string name, IntPtr file, uint flags);
    [DllImport("kernel32", CharSet=CharSet.Ansi)] static extern IntPtr GetProcAddress(IntPtr dll,string name);
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate byte InitFn();
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate void VoidFn();
    [UnmanagedFunctionPointer(CallingConvention.Cdecl)] delegate IntPtr InterfaceFn();
    [UnmanagedFunctionPointer(CallingConvention.ThisCall)] delegate byte BoolFn(IntPtr self);
    [UnmanagedFunctionPointer(CallingConvention.ThisCall)] delegate uint UintFn(IntPtr self);
    // CSteamID is returned through a hidden result pointer by this x86 C++ ABI.
    [UnmanagedFunctionPointer(CallingConvention.ThisCall)] delegate IntPtr IdFn(IntPtr self, out ulong id);
    [UnmanagedFunctionPointer(CallingConvention.ThisCall)] delegate byte SendFn(IntPtr self,ulong peer,byte[] data,uint size,int reliable,int channel);
    [UnmanagedFunctionPointer(CallingConvention.ThisCall)] delegate byte AvailableFn(IntPtr self,out uint size,int channel);
    [UnmanagedFunctionPointer(CallingConvention.ThisCall)] delegate byte ReadFn(IntPtr self,[Out] byte[] data,uint capacity,out uint size,out ulong peer,int channel);
    [UnmanagedFunctionPointer(CallingConvention.ThisCall)] delegate byte CloseFn(IntPtr self,ulong peer);
    [UnmanagedFunctionPointer(CallingConvention.ThisCall)] delegate byte RelayFn(IntPtr self,byte allow);
    [UnmanagedFunctionPointer(CallingConvention.ThisCall)] delegate byte StateFn(IntPtr self,ulong peer,out Session state);
    [StructLayout(LayoutKind.Sequential,Pack=4)] public struct Session {
        public byte Active,Connecting,Error,Relay; public int BytesQueued,PacketsQueued; public uint RemoteIP; public ushort RemotePort;
    }
    IntPtr dll,net; VoidFn callbacks,shutdown; bool initialized;
    SendFn send; AvailableFn available; ReadFn read; CloseFn close; StateFn state;
    public ulong ID {get;private set;} public uint AppID {get;private set;}
    public const int Channel=208;
    T Export<T>(string name) where T:class {
        IntPtr p=GetProcAddress(dll,name); if(p==IntPtr.Zero)throw new Exception("Missing Steam export: "+name);
        return Marshal.GetDelegateForFunctionPointer(p,typeof(T)) as T;
    }
    static T Method<T>(IntPtr obj,int slot) where T:class {
        if(obj==IntPtr.Zero)throw new Exception("Steam interface unavailable.");
        return Marshal.GetDelegateForFunctionPointer(Marshal.ReadIntPtr(Marshal.ReadIntPtr(obj),slot*IntPtr.Size),typeof(T)) as T;
    }
    public SteamProbe(string game,Action<string> log) {
        if(IntPtr.Size!=4)throw new Exception("This probe must run as x86.");
        string path=Path.Combine(Path.GetFullPath(game),"steam_api.dll");
        if(!File.Exists(Path.Combine(game,"OmertaSteam.exe"))||!File.Exists(path))throw new Exception("Select the installed Omerta folder.");
        Directory.SetCurrentDirectory(AppDomain.CurrentDomain.BaseDirectory);
        Environment.SetEnvironmentVariable("SteamAppId","208520");
        Environment.SetEnvironmentVariable("SteamGameId","208520");
        // LOAD_WITH_ALTERED_SEARCH_PATH: resolve the game's DLL dependencies beside it.
        dll=LoadLibraryEx(path,IntPtr.Zero,8);
        if(dll==IntPtr.Zero)throw new Exception("Could not load game's steam_api.dll: "+Marshal.GetLastWin32Error());
        log("Loaded installed game's Steam library.");
        shutdown=Export<VoidFn>("SteamAPI_Shutdown"); callbacks=Export<VoidFn>("SteamAPI_RunCallbacks");
        if(Export<InitFn>("SteamAPI_Init")()==0)throw new Exception("SteamAPI_Init failed. Run Steam online on an account owning Omerta, under the same Windows user as this probe.");
        initialized=true;
        try {
            log("SteamAPI_Init succeeded.");
            IntPtr user=Export<InterfaceFn>("SteamUser")();
            if(Method<BoolFn>(user,1)(user)==0)throw new Exception("Steam user is not connected online.");
            IntPtr utils=Export<InterfaceFn>("SteamUtils")();
            AppID=Method<UintFn>(utils,9)(utils);
            log("Steam app ID: "+AppID);
            if(AppID!=208520)throw new Exception("Unexpected app ID; stopping.");
            ulong id; Method<IdFn>(user,2)(user,out id); ID=id;
            if((ID>>56)!=1 || ((ID>>52)&15)!=1 || (uint)ID==0)throw new Exception("Invalid individual Steam identity returned; stopping.");
            log("Steam identity obtained.");
            net=Export<InterfaceFn>("SteamNetworking")();
            send=Method<SendFn>(net,0); available=Method<AvailableFn>(net,1); read=Method<ReadFn>(net,2);
            close=Method<CloseFn>(net,4); state=Method<StateFn>(net,6);
            if(Method<RelayFn>(net,7)(net,1)==0)throw new Exception("Steam refused relay enablement.");
            log("SteamNetworking005 available; relay fallback enabled.");
        } catch {Dispose();throw;}
    }
    public void Pump(){callbacks();}
    public bool Send(ulong peer,byte[] data){return send(net,peer,data,(uint)data.Length,2,Channel)!=0;}
    public bool Receive(out ulong peer,out byte[] data) {
        peer=0; data=null; uint size;
        if(available(net,out size,Channel)==0)return false;
        if(size>16448)throw new Exception("Oversized probe packet; stopping test.");
        data=new byte[size]; uint actual;
        if(read(net,data,size,out actual,out peer,Channel)==0)return false;
        if(actual!=size)Array.Resize(ref data,(int)actual);
        return true;
    }
    public int Queued(ulong peer) { Session s; return state(net,peer,out s)!=0 ? s.BytesQueued : 0; }
    public Session SessionInfo(ulong peer) { Session s; state(net,peer,out s); return s; }
    public string Status(ulong peer) {
        Session s; if(state(net,peer,out s)==0)return "No session yet";
        return "Active="+s.Active+" Connecting="+s.Connecting+" Error="+s.Error+" Relay="+s.Relay+" Queued="+s.BytesQueued;
    }
    public void Close(ulong peer){if(initialized&&close!=null&&peer!=0)close(net,peer);}
    public void Dispose(){if(initialized){initialized=false;shutdown();}}
}
