import Strong from '../../src/tags/strong'
import B from "../../src/tags/b";
import html2md from '../../src';

describe("test <strong></strong> tag",()=>{
  it('no nest',()=>{
    let strong=new Strong("<strong>strong</strong>")
    expect(strong.exec()).toBe("**strong**")
  })

  it('can nest',()=>{
    let strong=new Strong("<strong><i>strong and italic</i></strong>")
    expect(strong.exec()).toBe("***strong and italic***")
  })

  it('换行需要省略',()=>{
    let strong=new Strong("<strong>\n" +
      "<i>b and italic</i>\n" +
      "</strong>")
    expect(strong.exec()).toBe("***b and italic***")
  })
  it('和em重叠时需要空格',()=>{
    let test=html2md("<em>和为目标值</em><strong><code>target</code></strong>")
    expect(test).toBe("*和为目标值* **`target`**")
  })

  it('遇到match符号不需要空格',()=>{
    let test=html2md("**一个标题**<b>-- 第二个标题</b>")
    expect(test).toBe("\\*\\*一个标题\\*\\***\\-- 第二个标题**")
  })
})
