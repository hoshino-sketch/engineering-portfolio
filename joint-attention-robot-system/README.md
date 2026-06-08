# Joint Attention Robot System

卒業研究で作成した、人とロボットの共同注意に基づくロボット応答制御システムです。

## Overview

Webカメラを用いた視線推定結果から人の視線方向を取得し、ロボットの注視方向と照合することで共同注意の成立状態を判定しました。  
判定結果に応じて、ロボットのうなずきや首振り動作を切り替えました。


## Demo

- [共同注意デモ動画](https://drive.google.com/file/d/1vVhkX6adO88pbrH8aAt_SDmWpA46HQBO/view?usp=drive_link)  
  視線情報に基づいて共同注意の成立状態を判定し、ロボットが応答動作を切り替える様子を示しています。  
  本動画では、参加者がロボットと同じ対象へ視線を向けている状態を「共同注意成立」としています。

## Technologies

- Python
- ROS
- Linux
- ptgaze
- UDP通信
- CSVログ保存
- Sciurus17

## Files

- `src/gaze_data_sender.py`  
  ptgazeの出力から視線角度を取得し、制御プログラムへ送信するプログラムです。

- `src/gaze_robot_controller.py`  
  視線角度をもとに注視対象と共同注意の成立状態を判定し、ロボットの応答行動を制御するプログラムです。

## My Contributions

- 視線データ処理
- 共同注意判定
- ロボット制御
- 実験ログ保存
- 実験全体を統合する制御プログラムの実装

## Notes

本コードは卒業研究で使用した実験制御プログラムです。  
ROS、Sciurus17、ptgazeの実行環境に依存するため、一般環境ではそのまま動作しない可能性があります。  
実験参加者データやCSVログは含めていません。
