import { webview } from '@kit.ArkWeb';
import { hilog } from '@kit.PerformanceAnalysisKit';

@Entry
@Component
struct Index {
  controller: webview.WebviewController = new webview.WebviewController();
  @State pageTitle: string = 'SeeMap';
  @State panelOpen: boolean = false;

  build() {
    Column() {
      Row() {
        Text(this.pageTitle)
          .fontSize(18)
          .fontWeight(FontWeight.Bold)
          .fontColor('#FFFFFF')
          .margin({ left: 16 })
        Blank()
        Text('角色 × 声优 关系网络')
          .fontSize(12)
          .fontColor('#88FFFFFF')
          .margin({ right: 16 })
      }
      .width('100%')
      .height(48)
      .backgroundColor('#1a1a2e')

      Web({ src: $rawfile('index.html'), controller: this.controller })
        .width('100%')
        .layoutWeight(1)
        .javaScriptAccess(true)
        .domStorageAccess(true)
        .fileAccess(true)
        .onPageEnd(() => {
          try {
            this.controller.registerJavaScriptProxy({
              onPanelChange: (open: boolean) => {
                this.panelOpen = open;
              }
            }, 'seeMapNative', ['onPanelChange']);
          } catch (e) {
            hilog.error(0x0000, 'SeeMap', 'register proxy failed: %{public}s', JSON.stringify(e));
          }
        })
    }
    .width('100%')
    .height('100%')
    .backgroundColor('#0d0d17')
  }

  // 系统返回:有详情面板时先关面板,再退 App
  onBackPress(): boolean {
    if (this.panelOpen) {
      this.controller.runJavaScript('closePanel(); exitHighlight();');
      this.panelOpen = false;
      return true;
    }
    return false;
  }
}
