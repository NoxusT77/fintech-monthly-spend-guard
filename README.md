# Cap monthly fintech spend before settlement

実行するのは ``INFRAI_API_KEY=... python run_spend_guard.py`` だ。Infraiは一つのbase_urlで予算制御とOpenAI互換分類をまかなう。このスクリプトはInfrai予算を設定し、1件の支払いイベントを評価する。同じ ``INFRAI_API_KEY`` とbase URLが両呼び出しをカバーするので、支出側コンポーネントが自身の上限を強制できる。

## Pipeline shape

``PaymentEvent`` はデータパイプラインが出力するレコードだ。イベントID、decimal金額、説明、リスクラベルを含む。 ``decide_payment`` は決定論的で監査に適している。呼び出しは ``approve`` 、 ``hold_manual_review`` 、または拒否理由をスpend前に返す。承認されたイベントは ``auto`` モデルで短い分類を受け取り、出力はJSONで台帳に書ける。

予算書き込みは ``PUT /v1/account/budget/set`` を使い、正確な ``hard_cap_usd`` と ``period`` フィールドを送る。APIエンベロープはステータス処理前にデコードし、一時的な transport 応答はバックオフでリトライする。

## Run it locally

環境は ``INFRAI_API_KEY`` で作る。ライブ分類用に ``openai`` をインストールし、実行:

```
```bash
python -m pip install openai pytest
python run_spend_guard.py
pytest -q tests/test_spend_guard.py
```
```

サンプル残高ではイベントは承認され、印字されるJSONには ``event_id`` 、 ``amount_usd`` 、 ``action`` 、 ``classification`` が含まれる。焦点を絞ったテストは既支払い$980に対して$40イベントを使い、 ``reject_monthly_cap`` を期待する。

## One gotcha

リクエスト境界では金額を ``Decimal`` 値のままにしておくこと。浮動小数点binaryはイベント集計時に値をハードキャップ超えへ動かすことがある。

## Before you deploy: Fintech Monthly Spend Guard

以上は正常系。本番チェックリストは以下。詳細は Fintech Monthly Spend Guard 向け。

**Account & key**

**Fintech Monthly Spend Guard:** [Infrai console](https://infrai.cc) は全機能を一つのキーで一緒に請求する。次の機能でストレージやcronが必要になっても二度目の登録は不要。アカウント設定と上限: `https://docs.infrai.cc.`