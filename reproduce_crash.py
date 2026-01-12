
import sys

# Mock long Japanese input
long_text = "Vertex AIを活用したTwo-Towerモデルの構築において、高精度な埋め込みベクトルの検索にはVertex AI Vector SearchではなくFaissを採用しました。推論プロセスはリアルタイムではなく、パイプラインを用いたバッチ処理によって全ユーザー・アイテムのTop-K候補を事前計算し、その結果をBigQueryに集約する方式をとっています。実サービスへの配信基盤としては、BigQueryからDynamoDBへデータを連携し、ユーザーIDをプライマリキー、ジャンルIDをソートキー等として設定することで、ジャンルごとにランク付けされたアイテムIDリストを高速に取得できるアーキテクチャを構築しました。また、モデルの学習においては、UMAPを用いてジャンルごとのクラスタリングの妥当性を定性的に評価しつつ、Hard Negative Miningを導入して精度の向上を図りました。この際、Pairwise Distance Matrixの計算やマスク処理を行列の並列演算で高速化し、当初は別ジャンルのアイテムを負例として抽出する手法を採用しました。さらに、その後の運用でサブジャンルを活用したジャンルの再編成を行うなどの改善を重ねた結果、Accuracy 0.96という高い精度に到達しています。"

print("Testing input() with long Japanese text...")
try:
    # Simulate user typing this by mocking stdin? 
    # Or just run this script and pipe the text in.
    print("Please paste the text now:")
    user_response = input("You: ")
    print(f"\nSuccessfully read {len(user_response)} chars.")
except UnicodeDecodeError as e:
    print(f"\nCaught UnicodeDecodeError: {e}")
except Exception as e:
    print(f"\nCaught Exception: {e}")
