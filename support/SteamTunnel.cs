using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;

interface IPeerTransport : IDisposable {
    void Pump(); bool Send(byte[] data); bool Receive(out byte[] data); int Queued {get;}
}
sealed class SteamPeer : IPeerTransport {
    readonly SteamProbe api; readonly ulong peer; bool wasActive;
    public SteamPeer(SteamProbe api,ulong peer){this.api=api;this.peer=peer;}
    public void Pump(){api.Pump();var s=api.SessionInfo(peer);if(wasActive&&s.Error!=0)throw new Exception("Established Steam session failed (error "+s.Error+"). Restart both bridges to avoid continuing a damaged game stream.");if(s.Active!=0)wasActive=true;}
    public bool Send(byte[] data){return api.Send(peer,data);}
    public int Queued {get{return api.Queued(peer);}}
    public bool Receive(out byte[] data){for(int i=0;i<32;i++){ulong from;if(!api.Receive(out from,out data))return false;if(from==peer)return true;}data=null;return false;}
    public void Dispose(){api.Close(peer);}
}

// Ordered, bounded byte-stream tunnel. Every run and local TCP connection has a
// fresh ID, so delayed packets from earlier sessions cannot enter a new stream.
sealed class SteamTunnel : IDisposable {
    public const int Chunk=16384, Limit=4*1024*1024, Header=54;
    readonly IPeerTransport transport; readonly bool host; readonly int serverPort;
    readonly Action<string> log; readonly Guid local=Guid.NewGuid(); Guid remote,connection;
    TcpListener listener; Socket socket; readonly Queue<byte[]> writes=new Queue<byte[]>();
    int writeOffset,writeBytes; bool remoteClosing,disposed; long nextHello,lastReceived;
    bool started; public bool Ready {get;private set;} public int ListenPort {get;private set;}
    public long SentBytes {get;private set;} public long ReceivedBytes {get;private set;}
    public SteamTunnel(IPeerTransport transport,bool host,int serverPort,int listenPort,Action<string> log){
        this.transport=transport;this.host=host;this.serverPort=serverPort;this.log=log;
        if(!host){listener=new TcpListener(IPAddress.Loopback,listenPort);listener.Start(1);ListenPort=((IPEndPoint)listener.LocalEndpoint).Port;}
    }
    static Guid Id(byte[] b,int offset){byte[] id=new byte[16];Buffer.BlockCopy(b,offset,id,0,16);return new Guid(id);}
    public static bool Valid(byte[] b){return b!=null&&b.Length>=Header&&b.Length<=Header+Chunk&&b[0]==79&&b[1]==77&&b[2]==84&&b[3]==83&&b[4]==1&&b[5]>=1&&b[5]<=5;}
    byte[] Frame(byte kind,byte[] payload){
        byte[] b=new byte[Header+payload.Length];b[0]=79;b[1]=77;b[2]=84;b[3]=83;b[4]=1;b[5]=kind;
        Buffer.BlockCopy(local.ToByteArray(),0,b,6,16);Buffer.BlockCopy((kind==1?Guid.Empty:remote).ToByteArray(),0,b,22,16);
        Buffer.BlockCopy(connection.ToByteArray(),0,b,38,16);Buffer.BlockCopy(payload,0,b,Header,payload.Length);return b;
    }
    void Send(byte kind,byte[] payload){if(!transport.Send(Frame(kind,payload)))throw new Exception("Steam rejected tunnel data. Stop and restart the connection on both PCs.");}
    void Drop(){if(socket!=null){socket.Dispose();socket=null;}writes.Clear();writeOffset=writeBytes=0;remoteClosing=false;connection=Guid.Empty;}
    void Handle(byte[] b,long now){
        if(!Valid(b))throw new Exception("Invalid Steam tunnel packet or incompatible version.");
        Guid sender=Id(b,6);byte kind=b[5];
        if(kind==1){
            if(b.Length!=Header+1||sender==Guid.Empty||b[Header]!=(host?(byte)0:(byte)1))throw new Exception("Both players must choose opposite Host / Join roles.");
            if(remote!=Guid.Empty&&remote!=sender)throw new Exception("The other bridge restarted. Stop and restart this connection too.");
            remote=sender;lastReceived=now;Send(2,new byte[0]);return;
        }
        if(sender!=remote||Id(b,22)!=local)return; // stale or unrelated session
        lastReceived=now;
        if(kind==2){if(b.Length!=Header)throw new Exception("Invalid readiness packet.");if(!Ready){Ready=true;log("Steam connection ready. You can launch Omerta on both PCs.");}return;}
        if(!Ready)return;
        Guid conn=Id(b,38);
        if(kind==3){
            if(!host||b.Length!=Header||conn==Guid.Empty)throw new Exception("Invalid stream-open packet.");
            if(socket!=null)throw new Exception("A guest game connection is already open.");
            connection=conn;
            try{socket=new Socket(AddressFamily.InterNetwork,SocketType.Stream,ProtocolType.Tcp);socket.Connect(IPAddress.Loopback,serverPort);socket.NoDelay=true;socket.Blocking=false;log("Guest game connected to host helper through Steam.");}
            catch{Send(5,new byte[0]);Drop();throw;}
        } else if(conn==connection&&socket!=null){
            if(kind==5){if(b.Length!=Header)throw new Exception("Invalid close packet.");remoteClosing=true;}
            else if(kind==4){
                if(remoteClosing)throw new Exception("Data received after stream close.");
                int count=b.Length-Header;if(count==0)return;
                if(writeBytes+count>Limit)throw new Exception("Local game is not consuming data. Tunnel buffer limit reached.");
                byte[] part=new byte[count];Buffer.BlockCopy(b,Header,part,0,count);writes.Enqueue(part);writeBytes+=count;ReceivedBytes+=count;
            }
        }
    }
    public void Tick(long now){
        if(disposed)return;transport.Pump();if(!started){started=true;lastReceived=now;}
        if(now>=nextHello){nextHello=now+2000;Send(1,new byte[]{host?(byte)1:(byte)0});}
        for(int i=0;i<64;i++){byte[] b;if(!transport.Receive(out b))break;Handle(b,now);}
        if(now-lastReceived>(Ready?45000:120000))throw new Exception("Steam peer timed out. Both players should stop and reconnect.");
        if(!host&&listener.Pending()){
            Socket incoming=listener.AcceptSocket();
            if(!Ready||socket!=null){incoming.Dispose();log("Game connection rejected: wait for Steam connection ready before launching.");}
            else{socket=incoming;socket.NoDelay=true;socket.Blocking=false;connection=Guid.NewGuid();Send(3,new byte[0]);log("Local game connected to Steam tunnel.");}
        }
        if(socket==null)return;
        try {
            for(int i=0;i<32&&writes.Count>0&&socket.Poll(0,SelectMode.SelectWrite);i++){
                byte[] part=writes.Peek();int n=socket.Send(part,writeOffset,part.Length-writeOffset,SocketFlags.None);
                if(n==0)break;writeOffset+=n;writeBytes-=n;if(writeOffset==part.Length){writes.Dequeue();writeOffset=0;}
            }
            if(remoteClosing&&writes.Count==0){Drop();log("Remote game connection closed.");return;}
            for(int i=0;i<16&&!remoteClosing&&transport.Queued<Limit&&socket.Poll(0,SelectMode.SelectRead);i++){
                byte[] data=new byte[Chunk];int n=socket.Receive(data);
                if(n==0){Send(5,new byte[0]);Drop();log("Local game connection closed.");return;}
                Array.Resize(ref data,n);Send(4,data);SentBytes+=n;
            }
        } catch(SocketException e){if(e.SocketErrorCode==SocketError.WouldBlock)return;Send(5,new byte[0]);Drop();log("Game socket closed: "+e.SocketErrorCode);}
    }
    public void Dispose(){if(disposed)return;disposed=true;Drop();if(listener!=null)listener.Stop();transport.Dispose();}
}
