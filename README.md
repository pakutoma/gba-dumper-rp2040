# gba-dumper-rp2040
## 概要
RP2040マイコンを使ったゲームボーイアドバンスのROM吸い出し機の**実験的**実装です。  
MicroPythonで書かれており、PIOやDMAによって吸い出しの高速化を図っています。  
吸い出し速度は300KB/sほどです。

## 内容
- /board ROM吸い出し機基板のKiCadプロジェクト
- /client RP2040側プログラム
- host.py ホスト側プログラム

## 作成に必要なパーツ
- メイン基板（/board のKiCadプロジェクト）
  - PCBプロトタイプ業者（JLCPCB等）に発注してください
  - （多分余っているので、ぱくとまの知り合いなら渡します）
- 秋月電子通商 RP2040マイコンボードキット AE-RP2040
  - https://akizukidenshi.com/catalog/g/g117542/
  - Pi Pico用の最新のMicroPythonファームウェアを当ててください
- 1.5mmピッチ32ピンソケット（GB/GBA用）
  - AliExpressとかで買うといいです
- ピンソケット
  - AE-RP2040を直接ハンダ付けもできますが、あるとなにかと便利です
- クッションゴム（ダイソー等）
  - 基板の裏に貼るといいです

## 使い方
1. `mpremote` 等でボードに/clientの中身を書き込む
2. host.pyを開いて`ROM_SIZE`を設定し、実行する
3. 300KB/sくらいでROMが吸い出されます

## 対応ROM
- 通常のROMは吸い出せるはず
  - 手元にあったものは吸い出せました

## 非対応ROM
- 動かないもの

## 既知の不具合
- ソケットのフットプリントが合っていないので、はんだ付け時に加工が必要です
  - 修正予定です

## 免責事項
- 実験的な実装なので、まともに吸い出せない可能性があります
  - 吸い出したファイルは[ROM Checker](http://mrchecker.web.fc2.com/checker/rom_checker.html)等による検証をおすすめします

## 参考にしたもの
- [GBATEK](http://problemkaputt.de/gbatek.htm)
- [Gameboy Advance ROM Dumper mit Arduino Uno](https://robinwieschendorf.de/posts/2016/04/gameboy-advance-rom-dumper-mit-arduino-uno/)
- [Arduino Based GBA ROM Dumper - Part 1](https://douevenknow.us/post/68126856498/arduino-based-gba-rom-dumper-part-1)

## ライセンス
Apache License 2.0