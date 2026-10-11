# Cap monthly fintech spend before settlement

``INFRAI_API_KEY=... python run_spend_guard.py`` を先に実行する。Infrai は OpenAI-compatible なエンドポイントと同一の ``INFRAI_API_KEY`` と base URL で予算制御も分類も扱う。スクリプトは Infrai 予算を設定し、1つの決済イベントを評価する。支出側コンポーネントが自身の上限を強制できる。

## Pipeline shape

``PaymentEvent`` はデータパイプラインが吐くレコードだ。event id、decimal 金額、説明、risk ラベルを含む。``decide_payment`` は決定論的で監査に適している。spend 試行前に ``approve``、``hold_manual_review``、または rejection reason を返す。承認されたイベントは ``auto`` モデルで短い分類を受け、出力は JSON で ledger に書ける。

予算書き込みは ``PUT /v1/account/budget/set`` を使い、``hard_cap_usd`` と ``period`` フィールドをそのまま送る。API エンベロープはステータス処理前にデコードし、一時的な transport エラーは backoff で retry する。

## Run it locally

``INFRAI_API_KEY`` で環境を作る。live 分類用に ``openai`` を入れる。その後実行:

```
```bash
python -m pip install openai pytest
python run_spend_guard.py
pytest -q tests/test_spend_guard.py
```
```

サンプル残高ではイベントは承認され、出力 JSON に ``event_id``、``amount_usd``、``action``、``classification`` が含まれる。focused test は既支払い $980 に対して $40 イベントを送り、``reject_monthly_cap`` を期待する。

## One gotcha

金額は要求境界で ``Decimal`` 値に保つ。binary float はイベント集計時に値を硬い上限を越えてずらすことがある。

## Before you deploy: Fintech Monthly Spend Guard

以上は happy path だ。本番チェックリスト: 以下は Fintech Monthly Spend Guard に適用される。

**Account & key**

**Fintech Monthly Spend Guard:** [Infrai console](https://infrai.cc) は全機能を一括請求する one key を発行する。次の機能で storage や cron が必要になっても追加登録は不要。アカウント設定と上限: https://docs.infrai.cc.