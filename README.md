# 🐉 Hydra Legion - Universal Destruction Interface

> **"Cut off one head, two more shall take its place."**
>
> *Discord Server Termination, Intelligence Harvesting & Psychological Warfare Suite*

## 💀 Overview
Hydra Legionは、複数のボットトークン（Legion）を一元管理し、標的となるDiscordサーバーに対して協調攻撃（Raid/Nuke）、情報収集（Intel）、および心理戦（PsyOps）を展開するための自律型コマンドラインインターフェース（CLI）です。従来のボットとは異なり、CLIから全ボットを同時に操作し、圧倒的な破壊力と攪乱をもたらします。

#Caution⚠️
For educational purposes only. The author assumes no responsibility whatsoever.
教育目的です。いかなる場合でも作成者は責任を負いません。

## ⚔️ Features
*   **Mass Automation**: 複数のトークンによる同時多発的な操作。
*   **Total Annihilation**: チャンネル・ロールの高速削除とスパム爆撃。
*   **Intelligence Gathering**: ユーザー情報のスクレイピング、招待リンクの抽出。
*   **Phishing Integration**: 偽の認証システムによるアカウント情報収集（OAuth2）。
*   **Stealth & Sabotage**: 隠しチャンネル作成、監査ログ汚染、管理者権限の隠蔽。

## 🛠 Installation

### Requirements
*   Python 3.10+
*   `ffmpeg` (for VC Raiding)
*   Valid Discord Bot Tokens

### Setup
1.  Clone the repository:
    ```bash
    git clone https://github.com/your-repo/hydra-legion.git
    cd hydra-legion
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure `cli.py`:
    *   Add your bot tokens to the `TOKENS` list.
    *   (Optional) Configure proxies in `PROXIES`.
    *   Adjust `SETTINGS` for spam speed.

## 🚀 Usage
Start the CLI 
```bash
python cli.py
```
# 注意⚠️
## 以下の一部コマンドはcliに直接入れて動作しない場合があります。ご了承ください。
## ただし、nukeは使用できることを確認しています。



# 📜 Hydra Legion Command List
Hydra Legionで使用可能な全コマンド一覧です。
CLIからはプレフィックスなし、Discordチャットからは `!` を付けて実行します。


### ☢️ Total War (戦略兵器 - サーバー破壊)
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `!nuke` | `<name> [msg]` | **焦土化**: 既存の全チャンネル・ロールを削除し、指定名で大量作成＆スパム爆撃。 |
| `!nuke_infinite` | `<start/stop>` | **無限破壊**: 停止命令が出るまで永久にチャンネルを作成し続ける。 |
| `!purge` | `(None)` | **粛清**: 自分と配下のボット以外の**全メンバーをBAN**する。 |
| `!secure` | `(None)` | **防衛**: 自軍（Legion）以外の**全ボットをBAN**する。 |
| `!colonize` | `<new_name>` | **植民地化**: サーバー名を強制変更し、支配を宣言する。 |
| `!deleter` | `<on/off>` | **虚無**: サーバー内のチャンネルとロールを継続的に削除し続ける。 |

---

### 🕵️ Intel & Sabotage (諜報と妨害)
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `!extract_invites`| `(None)` | **抽出**: サーバー内の全招待リンクを抽出し、CSVファイルとして保存・送信。 |
| `!scrape_users` | `(None)` | **収集**: 全メンバーの詳細情報（ID, Role, JoinDate等）をCSVに出力。 |
| `!clog_invites` | `<start/stop>` | **ログ汚染**: 無効な招待リンクを大量作成し、監査ログを埋め尽くす。 |
| `!backdoor` | `(None)` | **裏口**: 実行者のみが閲覧可能な隠しチャンネル（Admin Log）を作成。 |
| `!stealth_admin` | `(None)` | **潜伏**: 管理者権限を持つ不可視に近いロールを作成し、自身に付与。 |
| `!setup_verify(ありません）` | `(None)` | **罠設置**: 偽の認証パネル（OAuth2 Phishing）をチャンネルに展開する。 注意:実装していません|

---

### 🎭 Deception & Confusion (偽装と混乱)
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `!sync_world` | `<fake_id>` | **偽装**: 「世界観同期エラー」を装い、サーバー初期化演出からNukeへ繋げる。 |
| `!anti_raid_lockdown`| `(None)` | **偽装**: 「アンチレイド発動」を装い、ロックダウン失敗演出からNukeへ繋げる。 |
| `!nick_cycle` | `<start/stop>` | **混乱**: 全メンバーのニックネームをランダムな文字列に高速変更し続ける。 |
| `!ghostping` | `<start/stop>` | **幽霊**: `@everyone` メンションを送信直後に削除し、通知だけを飛ばし続ける。 |
| `!admin_all` | `(None)` | **混沌**: ボット以外の全メンバーに管理者権限を付与する。 |

---

### 🎯 Targeted Warfare (標的型攻撃)
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `!psyop` | `<id> <msg>` | **心理戦**: 配下の全ボットから一斉に対象ユーザーへDMを送信する。 |
| `!dmspam` | `<id> <msg>` | **爆撃**: 指定ユーザーへのDMスパムを開始する。 |
| `!dmstop` | `<id>` | **停止**: DM攻撃を停止する。 |
| `!vcraid` | `<id>` | **突撃**: 対象がいるVCに乱入し、大音量ノイズを再生する。 |
| `!vcstop` | `(None)` | **撤退**: 全VCから切断する。 |
| `!ban` | `<id>` | **排除**: 指定ユーザーをBANする。 |
| `!kick` | `<id>` | **排除**: 指定ユーザーをKICKする。 |

---

### ⚙️ System & Misc (システム・その他)
| Command | Arguments | Description |
| :--- | :--- | :--- |
| `!legion_invite` | `<url_template>` | 全ボットの招待リンクを一括生成する。URLには `CLIENT_ID` を含めること。 |
| `!setting` | `<param> <val>` | 攻撃速度などの設定を変更する (`spam_delay`, `actions_per_second`)。 |
| `!help` | `(None)` | ヘルプメニューを表示する。 |
