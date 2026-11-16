const vscode = require('vscode');
function activate(ctx){
  ctx.subscriptions.push(vscode.commands.registerCommand('apiHunter.hunt', async ()=>{
    const kw = await vscode.window.showInputBox({prompt: "Keyword", value: "weather"});
    if(!kw) return;
    const term = vscode.window.createTerminal("API Hunter");
    term.sendText(`python3 apihunter.py run -k ${kw} -n 30`);
    term.show();
  }));
}
exports.activate = activate;
