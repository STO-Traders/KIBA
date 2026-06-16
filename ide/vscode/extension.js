// KIBA — VS Code extension. Drives KIBA's headless mode (`kiba -p ... --output-format json`)
// from the editor: ask questions, ask about a selection, run autonomously on a file, or open
// a KIBA terminal. No bundled model — it uses your configured KIBA install.

const vscode = require('vscode');
const cp = require('child_process');

let channel;

function cfg() {
  return vscode.workspace.getConfiguration('kiba');
}

function workspaceDir() {
  const folders = vscode.workspace.workspaceFolders;
  if (folders && folders.length) return folders[0].uri.fsPath;
  const ed = vscode.window.activeTextEditor;
  if (ed && ed.document.uri.scheme === 'file') {
    return require('path').dirname(ed.document.uri.fsPath);
  }
  return process.cwd();
}

// Run `kiba -p <prompt>` headlessly and resolve the parsed JSON envelope (or plain text).
function runKiba(prompt, opts) {
  opts = opts || {};
  return new Promise((resolve) => {
    const bin = cfg().get('binaryPath') || 'kiba';
    const maxTurns = String(cfg().get('maxTurns') || 30);
    const args = ['-p', prompt, '--output-format', 'json', '--max-turns', maxTurns];
    const env = Object.assign({}, process.env);
    if (opts.autonomous && cfg().get('autoApprove')) {
      env.KIBA_AUTO_APPROVE = '1';
      env.KIBA_TRUSTED_DIRS = workspaceDir();
    }
    let out = '';
    let err = '';
    let proc;
    try {
      proc = cp.spawn(bin, args, { cwd: workspaceDir(), env });
    } catch (e) {
      resolve({ error: 'Failed to launch KIBA: ' + e.message + ' (check kiba.binaryPath).' });
      return;
    }
    proc.stdout.on('data', (d) => { out += d.toString(); });
    proc.stderr.on('data', (d) => { err += d.toString(); });
    proc.on('error', (e) => resolve({ error: 'Failed to launch KIBA: ' + e.message + ' (set kiba.binaryPath).' }));
    proc.on('close', () => {
      const trimmed = out.trim();
      try {
        resolve(JSON.parse(trimmed));
      } catch (_) {
        resolve({ result: trimmed || err.trim() || '(no output)' });
      }
    });
  });
}

async function report(header, res) {
  channel.show(true);
  channel.appendLine('\n❯ ' + header);
  if (res.error) {
    channel.appendLine('⚠ ' + res.error);
    vscode.window.showErrorMessage('KIBA: ' + res.error);
  } else {
    channel.appendLine(res.result || JSON.stringify(res, null, 2));
  }
}

async function withProgress(title, fn) {
  return vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title, cancellable: false },
    fn
  );
}

async function ask(prefill) {
  const prompt = await vscode.window.showInputBox({ prompt: 'Ask KIBA', value: prefill || '' });
  if (!prompt) return;
  await withProgress('KIBA thinking…', async () => {
    const res = await runKiba(prompt, { autonomous: false });
    await report(prompt, res);
  });
}

function activate(context) {
  channel = vscode.window.createOutputChannel('KIBA');
  context.subscriptions.push(
    channel,
    vscode.commands.registerCommand('kiba.ask', () => ask()),
    vscode.commands.registerCommand('kiba.askSelection', () => {
      const ed = vscode.window.activeTextEditor;
      const sel = ed ? ed.document.getText(ed.selection) : '';
      const lang = ed ? ed.document.languageId : '';
      ask(sel ? 'About this ' + lang + ' code:\n```' + lang + '\n' + sel + '\n```\n\n' : '');
    }),
    vscode.commands.registerCommand('kiba.runOnFile', async () => {
      const ed = vscode.window.activeTextEditor;
      if (!ed) { vscode.window.showWarningMessage('KIBA: no active file.'); return; }
      const file = ed.document.fileName;
      const task = await vscode.window.showInputBox({ prompt: 'KIBA — what should it do to ' + file + '?' });
      if (!task) return;
      await ed.document.save();
      await withProgress('KIBA working on file…', async () => {
        const res = await runKiba(task + '\n\nTarget file: ' + file, { autonomous: true });
        await report('(on ' + file + ') ' + task, res);
      });
    }),
    vscode.commands.registerCommand('kiba.openTerminal', () => {
      const bin = cfg().get('binaryPath') || 'kiba';
      const term = vscode.window.createTerminal({ name: 'KIBA', cwd: workspaceDir() });
      term.show();
      term.sendText(bin + ' --stream');
    })
  );
}

function deactivate() {}

module.exports = { activate, deactivate };
