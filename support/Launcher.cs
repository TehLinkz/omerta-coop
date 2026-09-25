using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;

class Launcher : Form {
    readonly string support = Path.Combine(AppDomain.CurrentDomain.BaseDirectory,"support");
    readonly JavaScriptSerializer json = new JavaScriptSerializer();
    ComboBox difficulty=new ComboBox(), game=new ComboBox(), role=new ComboBox(), mode=new ComboBox(), network=new ComboBox();
    TextBox player=new TextBox(), address=new TextBox(), log=new TextBox();
    CheckBox unlock=new CheckBox(), wasd=new CheckBox();
    NumericUpDown timer=new NumericUpDown();
    Label status=new Label(), iplabel=new Label();
    FlowLayoutPanel actions=new FlowLayoutPanel();
    TableLayoutPanel fields=new TableLayoutPanel();
    List<Dictionary<string,object>> adapters=new List<Dictionary<string,object>>();
    bool busy;
    static string S(Dictionary<string,object>d,string k,string fallback="") {return d.ContainsKey(k)&&d[k]!=null?Convert.ToString(d[k]):fallback;}
    static Dictionary<string,object> D(object o) {return (Dictionary<string,object>)o;}
    public Launcher() {
        Text="Omerta Co-op"; Size=new Size(790,790); MinimumSize=new Size(760,760);
        StartPosition=FormStartPosition.CenterScreen; Font=new Font("Segoe UI",10);
        BackColor=Color.FromArgb(245,242,235); AutoScaleMode=AutoScaleMode.Dpi;
        var main=new TableLayoutPanel {Dock=DockStyle.Fill,Padding=new Padding(24),ColumnCount=1,RowCount=5};
        main.RowStyles.Add(new RowStyle(SizeType.Absolute,70));main.RowStyles.Add(new RowStyle(SizeType.Absolute,355));
        main.RowStyles.Add(new RowStyle(SizeType.Absolute,105));main.RowStyles.Add(new RowStyle(SizeType.Absolute,40));main.RowStyles.Add(new RowStyle(SizeType.Percent,100));
        Controls.Add(main);
        var heading=new Label {Text="OMERTA  /  CO-OP\nHost a game or join a friend. LAN and Radmin / ZeroTier use the same patch.",AutoSize=false,Dock=DockStyle.Fill};
        main.Controls.Add(heading,0,0);
        fields.Dock=DockStyle.Fill;fields.ColumnCount=3;fields.RowCount=9;
        fields.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,130));fields.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));fields.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,96));
        for(int i=0;i<9;i++)fields.RowStyles.Add(new RowStyle(SizeType.Percent,11.11f));
        main.Controls.Add(fields,0,1);
        game.DropDownStyle=ComboBoxStyle.DropDown; AddRow(0,"Game folder",game);
        var browse=new Button {Text="Browse…",Dock=DockStyle.Fill};browse.Click+=(s,e)=>{using(var f=new FolderBrowserDialog()){if(f.ShowDialog()==DialogResult.OK)game.Text=f.SelectedPath;}};fields.Controls.Add(browse,2,0);
        AddRow(1,"Player name",player);player.MaxLength=40;
        role.DropDownStyle=ComboBoxStyle.DropDownList;role.Items.AddRange(new object[]{"Host","Join"});role.SelectedIndex=0;AddRow(2,"Play as",role);
        mode.DropDownStyle=ComboBoxStyle.DropDownList;mode.Items.AddRange(new object[]{"Home LAN","Radmin / ZeroTier"});mode.SelectedIndex=0;AddRow(3,"Network",mode);
        network.DropDownStyle=ComboBoxStyle.DropDownList;AddRow(4,"Host interface",network);
        AddRow(5,"Host IP",address);address.Text="192.168.0.72";
        timer.Maximum=3600;timer.Width=90;timer.Dock=DockStyle.Left;AddRow(6,"Turn seconds",timer);
        fields.Controls.Add(new Label {Text="0 = off",Dock=DockStyle.Fill,TextAlign=ContentAlignment.MiddleLeft},2,6);
        var opts=new FlowLayoutPanel {Dock=DockStyle.Fill,WrapContents=false};
        unlock.Text="Unlocks + level 12";unlock.AutoSize=true;unlock.Checked=true;
        wasd.Text="WASD + arrows";wasd.AutoSize=true;wasd.Checked=true;opts.Controls.Add(unlock);opts.Controls.Add(wasd);
        AddRow(7,"Game options",opts);fields.SetColumnSpan(opts,2);
        difficulty.DropDownStyle=ComboBoxStyle.DropDownList;difficulty.Items.AddRange(new object[]{"Easy","Normal","Hard","Insane"});difficulty.SelectedIndex=1;AddRow(8,"Bot difficulty",difficulty);
        var tip=new ToolTip();tip.SetToolTip(difficulty,"Host controls both players. Easy: lower levels. Normal: original. Hard/Insane: enemy stat bonuses.");
        role.SelectedIndexChanged+=(s,e)=>RoleChanged();mode.SelectedIndexChanged+=(s,e)=>FillNetworks("");
        network.SelectedIndexChanged+=(s,e)=>{if(role.Text=="Host"&&network.SelectedItem is NetChoice)address.Text=((NetChoice)network.SelectedItem).IP;};
        actions.Dock=DockStyle.Fill;actions.WrapContents=true;main.Controls.Add(actions,0,2);
        ButtonAction("Install / update", "setup",true);ButtonAction("Save settings","save",true);
        ButtonAction("Play","play",false);ButtonAction("Play windowed","windowed",false);
        ButtonAction("Test connection","check",true);ButtonAction("Start host","start",true);ButtonAction("Stop host","stop",false);
        ButtonAction("Back up saves","backup",false);ButtonAction("Restore saves","restore",false);
        var refresh=new Button {Text="Refresh",AutoSize=true,Height=32};refresh.Click+=async(s,e)=>await RefreshState();actions.Controls.Add(refresh);
        status.Dock=DockStyle.Fill;status.Text="Finding Omerta in Steam libraries…";main.Controls.Add(status,0,3);
        log.Multiline=true;log.ReadOnly=true;log.ScrollBars=ScrollBars.Vertical;log.Dock=DockStyle.Fill;log.BackColor=Color.White;
        log.Text="Both PCs need matching timer settings. Unlocks use each character's default perks.\r\n";main.Controls.Add(log,0,4);
        Shown+=async(s,e)=>await RefreshState();FormClosing+=(s,e)=>{if(busy){e.Cancel=true;MessageBox.Show(this,"Wait for the current operation to finish.","Omerta Co-op");}};
    }
    void AddRow(int row,string label,Control c) {fields.Controls.Add(new Label {Text=label,Dock=DockStyle.Fill,TextAlign=ContentAlignment.MiddleLeft},0,row);c.Dock=DockStyle.Fill;c.Margin=new Padding(3,5,3,5);fields.Controls.Add(c,1,row);}
    void RoleChanged(){bool host=role.Text=="Host";mode.Enabled=host;network.Enabled=host;difficulty.Enabled=host;address.ReadOnly=host;if(host&&network.SelectedItem is NetChoice)address.Text=((NetChoice)network.SelectedItem).IP;}
    class NetChoice {public string IP,Alias;public override string ToString(){return Alias+" — "+IP;}}
    void FillNetworks(string preferred){network.Items.Clear();bool vpn=mode.SelectedIndex==1;foreach(var a in adapters){string alias=S(a,"InterfaceAlias");bool isVpn=alias.IndexOf("radmin",StringComparison.OrdinalIgnoreCase)>=0||alias.IndexOf("zerotier",StringComparison.OrdinalIgnoreCase)>=0||alias.IndexOf("tailscale",StringComparison.OrdinalIgnoreCase)>=0;if(isVpn!=vpn)continue;if(!vpn&&(alias.IndexOf("virtual",StringComparison.OrdinalIgnoreCase)>=0||alias.IndexOf("vmware",StringComparison.OrdinalIgnoreCase)>=0||alias.IndexOf("vethernet",StringComparison.OrdinalIgnoreCase)>=0))continue;network.Items.Add(new NetChoice {IP=S(a,"IPAddress"),Alias=alias});}if(network.Items.Count>0)network.SelectedIndex=0;for(int i=0;i<network.Items.Count;i++)if(((NetChoice)network.Items[i]).IP==preferred)network.SelectedIndex=i;}
    void SetBusy(bool value){busy=value;fields.Enabled=!value;actions.Enabled=!value;UseWaitCursor=value;}
    async Task<Dictionary<string,object>> Call(Dictionary<string,object> q){string request=json.Serialize(q);return await Task.Run(()=>{var p=new Process();p.StartInfo=new ProcessStartInfo(Path.Combine(support,"runtime","OmertaCoopServer.exe"),"\""+Path.Combine(support,"gui_bridge.py")+"\""){UseShellExecute=false,CreateNoWindow=true,RedirectStandardInput=true,RedirectStandardOutput=true,RedirectStandardError=true,WorkingDirectory=support,StandardOutputEncoding=Encoding.UTF8,StandardErrorEncoding=Encoding.UTF8};p.StartInfo.EnvironmentVariables["PYTHONIOENCODING"]="utf-8";p.Start();var err=p.StandardError.ReadToEndAsync();p.StandardInput.Write(request);p.StandardInput.Close();string output=p.StandardOutput.ReadToEnd();p.WaitForExit();string error=err.Result;p.Dispose();try{return json.Deserialize<Dictionary<string,object>>(output);}catch{throw new Exception("Helper returned an unexpected response. "+error+output);}});}
    async Task RefreshState(){SetBusy(true);try{var r=await Call(new Dictionary<string,object>{{"action","status"}});if(!(bool)r["ok"])throw new Exception(S(r,"error"));var d=D(r["data"]);game.Items.Clear();foreach(object g in ((System.Collections.IEnumerable)d["games"]).Cast<object>())game.Items.Add(g);game.Text=S(d,"game");var cfg=D(d["settings"]);var host=D(d["host"]);player.Text=S(cfg,"name","Player");difficulty.SelectedIndex=Math.Max(0,Array.IndexOf(new string[]{"easy","normal","hard","insane"},S(cfg,"difficulty","normal")));unlock.Checked=S(cfg,"maxed","1")=="1";wasd.Checked=S(cfg,"wasd","1")=="1";decimal n;timer.Value=decimal.TryParse(S(cfg,"turn_seconds","0"),out n)?Math.Max(0,Math.Min(3600,n)):0;role.SelectedIndex=S(cfg,"host","127.0.0.1")=="127.0.0.1"?0:1;mode.SelectedIndex=S(host,"mode")=="VPN"?1:0;adapters=((System.Collections.IEnumerable)d["adapters"]).Cast<object>().Select(D).ToList();FillNetworks(S(host,"host"));if(role.Text=="Join")address.Text=S(cfg,"host");RoleChanged();status.Text=(game.Text.Length==0?"Omerta not found — choose its folder.":"Omerta found. ")+((bool)d["running"]?"Host helper is running.":"");}catch(Exception ex){ShowError(ex.Message);}finally{SetBusy(false);}}
    void ButtonAction(string text,string action,bool settings){var b=new Button {Text=text,AutoSize=true,Height=32,Margin=new Padding(3)};b.Click+=async(s,e)=>{var q=new Dictionary<string,object>{{"action",action}};if(settings){q["game"]=game.Text;q["name"]=player.Text;q["role"]=role.Text;q["mode"]=mode.SelectedIndex==0?"LAN":"VPN";q["address"]=address.Text;q["interface"]=network.SelectedItem is NetChoice?((NetChoice)network.SelectedItem).Alias:"";q["options"]=new Dictionary<string,object>{{"turn_seconds",timer.Value.ToString()},{"maxed",unlock.Checked?"1":"0"},{"wasd",wasd.Checked?"1":"0"},{"difficulty",difficulty.Text.ToLowerInvariant()}};}if(action=="restore"){using(var dialog=new OpenFileDialog {Filter="Host backup (*.zip)|*.zip"}){if(dialog.ShowDialog()!=DialogResult.OK)return;q["path"]=dialog.FileName;}}SetBusy(true);status.Text=text+"…";try{var r=await Call(q);string details=S(r,"log");if(details.Length>0)log.AppendText(details.Replace("\n","\r\n")+"\r\n");if(!(bool)r["ok"])throw new Exception(S(r,"error"));status.Text=S(D(r["data"]),"message","Completed.");if(action=="setup"&&role.Text=="Host")status.Text="Ready. Your friend joins "+address.Text; }catch(Exception ex){ShowError(ex.Message);}finally{SetBusy(false);}};actions.Controls.Add(b);}
    void ShowError(string error){status.Text="Could not complete.";log.AppendText(error+"\r\n");MessageBox.Show(this,error,"Omerta Co-op",MessageBoxButtons.OK,MessageBoxIcon.Warning);}
    [STAThread] static void Main(string[] args){Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);if(args.Contains("--self-test")){using(var f=new Launcher()){f.CreateControl();if(f.Controls.Count!=1||f.actions.Controls.Count!=10)Environment.Exit(2);var pending=f.Call(new Dictionary<string,object>{{"action","status"}});while(!pending.IsCompleted){Application.DoEvents();System.Threading.Thread.Sleep(10);}var r=pending.GetAwaiter().GetResult();if(!(bool)r["ok"])Environment.Exit(3);var d=D(r["data"]);foreach(object g in (System.Collections.IEnumerable)d["games"])if(!File.Exists(Path.Combine(g.ToString(),"OmertaSteam.exe")))Environment.Exit(4);f.adapters=((System.Collections.IEnumerable)d["adapters"]).Cast<object>().Select(D).ToList();f.FillNetworks("");}return;}Application.Run(new Launcher());}
}
