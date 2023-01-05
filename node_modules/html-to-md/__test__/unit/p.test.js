import html2md from '../../src'
import P from '../../src/tags/p'
import config from '../../src/config'

config.set({renderCustomTags:true})

describe('test <p></p> tag',()=>{
  it('textNode',()=>{
    let p=new P("<p>This is paragraph</p>")
    expect(p.exec()).toBe("\nThis is paragraph\n")
  })
  it('nest',()=>{
    let p=new P("<p><b>bold</b></p>")
    expect(p.exec()).toBe("\n**bold**\n")
  })

  it('nest2',()=>{
    let p=new P("<p><s><f>SD<f>S<f>SDF&lt;&gt;S<f>SDF&lt;&gt;</f></f></f></f></s></p>")
    expect(p.exec()).toBe('\n' +
      '~~<f>SD<f>S<f>SDF&lt;&gt;S<f>SDF&lt;&gt;</f></f></f></f>~~\n')
  })

  it('p tag inside string, should have extra gap',()=>{
    let p=new P("<p>一款集成了模拟和拦截<p>请求并拥有一</p>定编程能力的谷歌浏览器插件...</p>")
    expect(p.exec()).toBe("\n" +
        "一款集成了模拟和拦截\n" +
        "\n" +
        "请求并拥有一\n" +
        "\n" +
        "定编程能力的谷歌浏览器插件...\n")
  })

  it('p tag gaps 1',()=>{
    let str=html2md("<p>1234</p>&nbsp;\n\n\n\n&nbsp;<p>5678</p>")
    expect(str).toBe("1234\n\n5678")
  })

  it('p tag gaps 2',()=>{
    let str=html2md("<p>1234</p>&nbsp;&nbsp;<p>5678</p>")
    expect(str).toBe("1234\n\n5678")
  })
})
