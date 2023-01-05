import html2Md from '../../src/index'
describe('test <em></em> tag',()=>{
  it('no nest',()=>{
    let em=html2Md("<em>javascript</em>")
    expect(em).toBe("*javascript*")
  })

  it('can nest',()=>{
    let em=html2Md("<em><strong>strong and italic</strong></em>")
    expect(em).toBe("***strong and italic***")
  })

  it('换行需要省略',()=>{
    let em=html2Md("<em>\n" +
      "<strong>strong and italic</strong>\n" +
      "</em>")
    expect(em).toBe("***strong and italic***")
  })

  it('和strong重叠时需要空格',()=>{
    let em=html2Md("<strong>和为目标值</strong><em><code>target</code></em>")
    expect(em).toBe("**和为目标值** *`target`*")
  })
})
