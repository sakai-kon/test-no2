# データベースの使い方

## ファイル構成

- `data/science.json`：理科の知識カードと確認問題
- `data/math.json`：数学の知識カードと確認問題
- `data/manifest.json`：教科ごとのファイル、件数、範囲のメタデータ
- `schema/knowledge-item.schema.json`：データの構造を検査するためのJSON Schema

## 1件のデータ

各 `items[]` は知識カードです。主なフィールドは次のとおりです。

- `id`：重複しない知識項目ID
- `unit_code` / `unit` / `topic`：単元とテーマ
- `explanation`：概要説明
- `key_points`：覚えるべきポイント
- `formulas`：公式（数学や必要な理科項目のみ）
- `questions[]`：確認問題、正答、解説、難易度、タグ

## ブラウザーで読み込む例

リポジトリをWebサイトとして配信する場合、同じサイト上にあるJSONファイルを `fetch` で読み込めます。

```js
async function loadSubject(subject) {
  const path = subject === "理科"
    ? "./data/science.json"
    : "./data/math.json";

  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`データの読み込みに失敗しました: ${response.status}`);
  }

  const database = await response.json();
  if (!Array.isArray(database.items)) {
    throw new Error("データ形式が正しくありません。");
  }
  return database;
}
```

## キーワード検索の例

```js
function searchItems(database, query) {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  return database.items.filter((item) => {
    const text = [
      item.unit,
      item.topic,
      item.explanation,
      ...(item.key_points ?? []),
      ...(item.keywords ?? []),
      ...(item.questions ?? []).flatMap((question) => [
        question.prompt,
        question.answer,
        ...(question.tags ?? [])
      ])
    ].join(" ").toLowerCase();

    return text.includes(q);
  });
}
```

## 問題の出題例

```js
function getQuestions(database, { unitCode, difficulty } = {}) {
  return database.items
    .filter((item) => !unitCode || item.unit_code === unitCode)
    .flatMap((item) => item.questions.map((question) => ({
      ...question,
      unit: item.unit,
      topic: item.topic,
      subject: item.subject
    })))
    .filter((question) =>
      difficulty == null || question.difficulty === difficulty
    );
}
```

## 保守・拡張ルール

1. 追加する項目・問題は、既存のIDと重複しないIDを付けます。
2. 正答だけでなく、学習者が理解できる解説も必ず記録します。
3. 問題文は独自作成し、教科書や市販問題集の文面をそのまま転記しません。
4. 学年配当や学習順序は学校・教科書で異なるため、授業で使う際は学校の年間計画と照合します。
5. 数値問題は、計算結果、単位、符号、式を確認してから追加します。
6. データを変更したらJSONの構文と必須フィールドを検証します。

## 網羅性について

これは継続的に拡張する初版です。中学1年相当の主要単元を広く扱いますが、あらゆる教科書・学校独自の発展課題まで含む完全なデータベースだと保証するものではありません。単元ごとに「知識」「典型問題」「応用問題」「実験・資料読み取り問題」を追加することで育てていく想定です。

範囲の確認には、文部科学省の[中学校学習指導要領解説](https://www.mext.go.jp/a_menu/shotou/new-cs/1387016.htm)を参照してください。
