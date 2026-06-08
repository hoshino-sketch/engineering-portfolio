# Wearable Device Game

研究室の6週間制作プロジェクトで制作した、装着型デバイスを用いた体験型ゲームです。  
ユーザーは手足に装着したデバイスの光を手がかりに、出題されたポーズへ近づきます。

## Screenshot

![PoseRing title screen](media/pose_ring_title_screen.png)

※ タイトル画面のUIデザインおよびビジュアル制作は、チーム内の別メンバーが担当しました。

## Demo

- [ポーズ出題者デモ動画](https://drive.google.com/file/d/1Xqc0f_wxPFXWYXqj-msFz2J5nz2OahM3/view?usp=drive_link)
  出題者側のデモ動画です。正解ポーズを設定する様子を示しています。

- [ポーズ回答者デモ動画](https://drive.google.com/file/d/1-SlCL6KXHPiziBa0QmUX0Zh4I-O0hYVJ/view?usp=drive_link)  
  回答者側のデモ動画です。装着型デバイスの光を手がかりに、出題ポーズへ近づく様子を示しています。

## Source Code

- `src/pose_ring_main_controller.py`

メインPC側で動作する制御プログラムです。  
Aセットの2台のWebカメラで色付きデバイスを検出し、サブPCから受信したBセットの3D座標も補助的に利用します。  
現在座標と目標座標を比較し、XIAOへBLE通信でLEDフィードバックを送信します。

## Technologies

- Python
- OpenCV
- Webカメラ
- 三角測量
- UDP通信
- BLE通信
- XIAO
- 基板加工
- 回路制作

## My Role

- プロジェクトマネージャーとして実現方法の整理と進捗管理
- 座標取得方法の検討
- 2台のWebカメラによる三角測量案の提案
- デバイス制作、基板加工、回路制作の一部

## Notes

- Webアプリ、マイコン書き込み用コード、Bカメラ側の座標推定コードはチームメンバーが担当したため、本リポジトリには掲載していません。
- キャリブレーション用コード、キャリブレーション画像、キャリブレーション結果ファイルは掲載していません。
