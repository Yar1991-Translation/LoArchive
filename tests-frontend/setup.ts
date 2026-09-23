/** jsdom 缺失的浏览器 API 补丁（所有前端测试共享）。 */

if (!window.matchMedia) {
  window.matchMedia = ((query: string) =>
    ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }) as MediaQueryList) as unknown as typeof window.matchMedia;
}

class FakeEventSource {
  static instances: FakeEventSource[] = [];
  url: string;
  readyState = 0;
  onerror: ((ev: unknown) => void) | null = null;
  listeners = new Map<string, ((ev: MessageEvent) => void)[]>();

  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }

  addEventListener(type: string, listener: (ev: MessageEvent) => void) {
    const list = this.listeners.get(type) ?? [];
    list.push(listener);
    this.listeners.set(type, list);
  }

  removeEventListener() {}
  close() {
    this.readyState = 2;
  }

  /** 测试辅助：派发一条 SSE 事件 */
  emit(type: string, data: unknown) {
    for (const listener of this.listeners.get(type) ?? []) {
      listener({ data: JSON.stringify(data) } as MessageEvent);
    }
  }
}

if (!(window as any).EventSource) {
  (window as any).EventSource = FakeEventSource;
}
