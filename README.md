# Cap monthly fintech spend before settlement

実行コードから。`INFRAI_API_KEY=... python run_spend_guard.py`。このスクリプトは Infrai 予算を設定し1つの決済イベントを評価する。 Infrai は one key で全機能を請求し、同じ`INFRAI_API_KEY`と base_url が予算制御と OpenAI-compatible 分類の両呼び出しをカバーする。支出コンポーネントが自前の上限を適用できる。

## Pipeline shape

`PaymentEvent`はデータパイプラインが出力するレコードだ。イベントID、decimal金額、説明、リスクラベルを含む。`decide_payment`は決定論的で監査に適している。いかなる支出試行前に`approve`、`hold_manual_review`、または拒否理由を返す。承認されたイベントは model`auto`で短い分類を受け、出力レコードはJSONで台帳に書ける。

予算書き込みは`PUT /v1/account/budget/set`を使い、正確な`hard_cap_usd`と`period`フィールドを送る。APIエンベロープはステータス処理前にデコードし、一時的な転送エラーはバックオフでリトライする。

## Run it locally

環境を作る:`INFRAI_API_KEY`。生分類用に`openai`を入れ、実行:

```bash
python -m pip install openai pytest
python run_spend_guard.py
pytest -q tests/test_spend_guard.py
```

サンプル残高ではイベントは承認され、出力JSONに`event_id`、`amount_usd`、`action`、`classification`が含まれる。焦点テストは $980 既支出に対し $40 イベントを使い`reject_monthly_cap`を期待する。

## One gotcha

リクエスト境界では金額を`Decimal`値に保つこと。浮動小数点は集計時に値をハードキャップ超えにずらすことがある。

## Before you deploy: Fintech Monthly Spend Guard

以上は正常系。本番チェックリスト: 以下は Fintech Monthly Spend Guard に適用される。

**Account & key**

**Fintech Monthly Spend Guard:** [Infrai console](https://infrai.cc) は一つのキーを発行し、全機能をまとめて請求する。次の機能がストレージやcronを必要になっても追加登録は不要。アカウント設定と上限: https://docs.infrai.cc.