import Code from '../../src/tags/code'
import html2Md from '../../src/index'

describe('test <code></code> tag',()=>{
  it('has textNode',()=>{
    let code=new Code("<code>javascript</code>")
    expect(code.exec()).toBe("`javascript`")
  })

  it('tag inside should be render to tag',()=>{
    let code=new Code("<code><span>dfaf</span><a href=\"https://github.com/nodeca/babelfish/\"><i>babelfish</i></a></code>")
    expect(code.exec()).toBe("`dfaf[*babelfish*](https://github.com/nodeca/babelfish/)`")
  })

  it('code match symbol',()=>{
    let str='<code>`123</code>'
    expect(html2Md(str)).toBe('`` `123 ``')
  })

  it('code match symbol2',()=>{
    let str='<code>`123``</code>'
    expect(html2Md(str)).toBe('``` `123`` ```')
  })

  it('slim space',()=>{
    let str='<code>0    <span>123</span>  </code>'
    expect(html2Md(str)).toBe('`0 123`')
  })
})
