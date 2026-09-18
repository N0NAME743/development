import * as vscode from 'vscode';

const SYSTEM_INSTRUCTION = `あなたはプロンプトエンジニアリングの専門家です。
ユーザーが書いた下書きのメモや思いつきを、生成AI（Claude や ChatGPT など）に渡すための
構造化されたプロンプトに書き直してください。

出力は次の見出しを持つ Markdown 形式にしてください（該当する情報が元の文章から
読み取れない見出しは省略して構いません）。

## 目的
## 背景・前提
## 制約条件
## 期待する出力

ルール:
- 元のテキストの言語（日本語）はそのまま維持すること。
- 元の文章に無い情報を勝手に創作しないこと。書かれていないことは補完せず、
  必要であれば「(要確認)」のように書いておくこと。
- 前置き・後書き・説明文は一切書かず、整形後のプロンプト本文のみを出力すること。`;

async function polishSelection(): Promise<void> {
	const editor = vscode.window.activeTextEditor;
	if (!editor) {
		vscode.window.showErrorMessage('アクティブなエディタがありません。');
		return;
	}

	const selection = editor.selection;
	if (selection.isEmpty) {
		vscode.window.showErrorMessage('整形したいテキストを選択してください。');
		return;
	}

	const originalText = editor.document.getText(selection);

	const models = await vscode.lm.selectChatModels();
	if (models.length === 0) {
		vscode.window.showErrorMessage(
			'利用可能な言語モデルが見つかりません。GitHub Copilot Chat などの拡張機能が有効になっているか確認してください。'
		);
		return;
	}
	const model = models[0];

	await vscode.window.withProgress(
		{
			location: vscode.ProgressLocation.Notification,
			title: 'プロンプトを整形しています…',
			cancellable: true,
		},
		async (_progress, token) => {
			const messages = [
				vscode.LanguageModelChatMessage.User(SYSTEM_INSTRUCTION),
				vscode.LanguageModelChatMessage.User(
					`以下が元の下書きテキストです。これを整形してください。\n\n---\n${originalText}\n---`
				),
			];

			try {
				const response = await model.sendRequest(messages, {}, token);
				let polished = '';
				for await (const fragment of response.text) {
					polished += fragment;
				}
				polished = polished.trim();

				if (!polished) {
					vscode.window.showWarningMessage('モデルから空の応答が返されました。変更は行いません。');
					return;
				}

				await editor.edit((editBuilder) => {
					editBuilder.replace(selection, polished);
				});
			} catch (err) {
				if (err instanceof vscode.LanguageModelError) {
					vscode.window.showErrorMessage(`プロンプトの整形に失敗しました: ${err.message}`);
				} else {
					vscode.window.showErrorMessage(`プロンプトの整形中に予期しないエラーが発生しました: ${String(err)}`);
				}
			}
		}
	);
}

export function activate(context: vscode.ExtensionContext): void {
	context.subscriptions.push(
		vscode.commands.registerCommand('promptPolisher.polishSelection', polishSelection)
	);
}

export function deactivate(): void {
	// no-op
}
