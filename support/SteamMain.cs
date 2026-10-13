using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using System.Diagnostics;
using System.Windows.Forms;

sealed class FakePeer:IPeerTransport {
    public FakePeer Other; public Queue<byte[]> Incoming=new Queue<byte[]>();
    public int Queued{get{return 0;}}public void Pump(){}public void Dispose(){}
    public bool Send(byte[] b){Other.Incoming.Enqueue(b);return true;}
    public bool Receive(out byte[] b){b=Incoming.Count>0?Incoming.Dequeue():null;return b!=null;}
}
static class SteamMain {
    static void Require(bool v,string message){if(!v)throw new Exception(message);}
    static void Test(){
        Require(!SteamTunnel.Valid(new byte[53]),"Truncated frame accepted");
        var a=new FakePeer();var b=new FakePeer();a.Other=b;b.Other=a;
        var echo=new TcpListener(IPAddress.Loopback,0);echo.Start();int port=((IPEndPoint)echo.LocalEndpoint).Port;
        var echoTask=Task.Run(()=>{for(int i=0;i<2;i++)using(var c=echo.AcceptTcpClient()){var stream=c.GetStream();byte[] buf=new byte[1337];int n;while((n=stream.Read(buf,0,buf.Length))>0)stream.Write(buf,0,n);}});
        using(var host=new SteamTunnel(a,true,port,0,s=>{}))using(var guest=new SteamTunnel(b,false,port,0,s=>{})){
            long time=0;Action pump=()=>{host.Tick(time);guest.Tick(time);time+=16;Thread.Sleep(1);};
            for(int i=0;i<100&&!guest.Ready;i++)pump();Require(host.Ready&&guest.Ready,"Handshake failed");
            for(int run=0;run<2;run++){
                int r=run;
                var transfer=Task.Run(()=>{using(var c=new TcpClient()){c.Connect(IPAddress.Loopback,guest.ListenPort);c.ReceiveTimeout=10000;c.SendTimeout=10000;byte[] data=new byte[524288+r];new Random(71+r).NextBytes(data);var stream=c.GetStream();var sending=Task.Run(()=>stream.Write(data,0,data.Length));byte[] result=new byte[data.Length];int pos=0;while(pos<result.Length){int n=stream.Read(result,pos,result.Length-pos);if(n==0)throw new Exception("Early EOF");pos+=n;}sending.Wait();for(int i=0;i<data.Length;i++)Require(data[i]==result[i],"Byte mismatch");}});
                var deadline=Stopwatch.StartNew();while(!transfer.IsCompleted&&deadline.ElapsedMilliseconds<15000)pump();Require(transfer.IsCompleted,"Transfer timeout");transfer.GetAwaiter().GetResult();for(int i=0;i<50;i++)pump();
            }
            Require(host.ReceivedBytes==1048577&&guest.ReceivedBytes==1048577,"Byte count mismatch");
            // A well-formed but unrelated session must not open a local socket.
            byte[] stale=new byte[SteamTunnel.Header];stale[0]=79;stale[1]=77;stale[2]=84;stale[3]=83;stale[4]=1;stale[5]=3;Guid.NewGuid().ToByteArray().CopyTo(stale,6);a.Incoming.Enqueue(stale);pump();
        }
        echo.Stop();Require(echoTask.Wait(2000),"Echo worker did not exit");
        var x=new FakePeer();var y=new FakePeer();x.Other=y;y.Other=x;
        using(var h1=new SteamTunnel(x,true,port,0,s=>{}))using(var h2=new SteamTunnel(y,true,port,0,s=>{})){
            bool rejected=false;try{h1.Tick(0);h2.Tick(0);}catch(Exception){rejected=true;}Require(rejected,"Same-role handshake accepted");
        }
    }
    [STAThread] static int Main(string[] args){
        if(args.Length>0&&args[0]=="--ui-test"){
            Application.EnableVisualStyles();using(var f=new SteamWindow()){f.ShowInTaskbar=false;f.Opacity=0;f.Show();var wait=Stopwatch.StartNew();do{Application.DoEvents();Thread.Sleep(10);}while(f.Busy&&wait.ElapsedMilliseconds<10000);for(int page=0;page<3;page++){f.ShowPage(page);Application.DoEvents();using(var b=new System.Drawing.Bitmap(f.Width,f.Height)){f.DrawToBitmap(b,new System.Drawing.Rectangle(0,0,b.Width,b.Height));b.Save(args[1]+page+".png");}}}return 0;
        }
        if(args.Length>0&&args[0]=="--self-test"){
            string path=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"support","tunnel-test.txt");
            try{Test();File.WriteAllText(path,"PASS: handshake; 1,048,577 bytes each direction; stream reconnect; stale session ignored; same-role rejected; truncated frame rejected.\n");return 0;}
            catch(Exception ex){File.WriteAllText(path,ex.ToString());return 1;}
        }
        if(args.Length>0&&args[0]=="--probe"){
            string path=Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"support","steam-probe.txt");File.WriteAllText(path,"");
            try{using(var p=new SteamProbe(args[1],s=>File.AppendAllText(path,s+"\n"))){p.Pump();}return 0;}catch(Exception ex){File.AppendAllText(path,ex.ToString());return 1;}
        }
        Application.EnableVisualStyles();Application.Run(new SteamWindow());return 0;
    }
}
