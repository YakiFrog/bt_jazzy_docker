# サンプルコードの解説 (`main.cpp`)

このプロジェクトに同梱されているサンプルコードの構造と、BehaviorTree.CPP v4 の基本的な考え方を解説します。

## プログラムの 3 つのステップ

Behavior Tree プログラミングは、大きく分けて **「部品を作る」「組み立てる」「動かす」** の 3 つのステップで構成されます。

---

### 1. 部品を作る (C++ ノードの定義)
Behavior Tree の最小単位である「ノード」を C++ クラスとして作成します。

```cpp
class SayHello : public SyncActionNode {
public:
    // ... コンストラクタ等 ...

    // ポートの定義（XML から値を受け取るための窓口）
    static PortsList providedPorts() {
        return { InputPort<std::string>("message") };
    }

    // ノードの実行ロジック
    NodeStatus tick() override {
        std::string msg;
        getInput("message", msg); // XML で指定されたメッセージを取得
        std::cout << "Robot says: " << msg << std::endl;
        return NodeStatus::SUCCESS; // 完了を報告
    }
};
```
- **`SyncActionNode`**: 短時間で完了するアクション（同期アクション）のベースクラス。
- **`tick()`**: このノードの実行順が回ってきたときに呼ばれるメインロジック。
- **`NodeStatus`**: 実行結果（SUCCESS, FAILURE, RUNNING）を返します。

### 2. 組み立てる (ファクトリへの登録とツリー生成)
作った C++ 部品を、設計図（XML）に基づいて組み立てます。

```cpp
BehaviorTreeFactory factory;

// C++ クラスを "SayHello" という名前で XML 上で使えるように登録
factory.registerNodeType<SayHello>("SayHello");

// XML ファイルを読み込んで、実行可能な「ツリー」を生成
auto tree = factory.createTreeFromFile("my_tree.xml");
```

### 3. 動かす (実行と可視化)
組み立てたツリーを動かし、その様子を外部ツール（Groot2）に送信します。

```cpp
// Groot2 送信用の中継役をインスタンス化
Groot2Publisher publisher(tree);

while (true) {
    // ツリーのルートから順にノードを実行
    tree.tickWhileRunning();
    
    // 2秒待機（ループの間隔）
    std::this_thread::sleep_for(std::chrono::seconds(2));
}
```

---

## 設計図 (`my_tree.xml`) の役割

Behavior Tree の最大の特徴は、**「機能（C++）」と「振る舞い（XML）」の分離**にあります。

```xml
<root BTCPP_format="4">
    <BehaviorTree ID="MainTree">
        <Sequence name="root_sequence">
            <SayHello message="Hello!"/>
            <SayHello message="Bye!"/>
        </Sequence>
    </BehaviorTree>
</root>
```

- **`Sequence`**: 制御ノードの一つ。子供のノードを左から順に実行し、一つでも失敗したらそこで中止します。
- **メリット**: プログラムをコンパイルし直すことなく、XML ファイルを書き換えるだけでロボットの挙動（挨拶の順番や条件）を変更できます。
