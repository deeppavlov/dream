import html2Md from '../../src/index'
import config from '../../src/config'

describe('清空指定的tag以及内部的标签',()=>{

  beforeEach(()=>{
    config.reset()
  })

  it('消除tag',()=>{
    expect(html2Md("<>abc</>",{emptyTags:['']})).toBe('abc')
  })

  it('跳过空白标签及其内部',()=>{
    expect(html2Md('<><b><i>abc</i></b></>',{emptyTags:['']})).toBe('abc')
  })

  it('消除b和i',()=>{
    expect(html2Md("<b><i>abc</i></b>",{emptyTags:['b','i']})).toBe('abc')
  })

  it('消除b和i(2)',()=>{
    expect(html2Md("<b><i>abc</i></b>",{emptyTags:['b']})).toBe('abc')
    // expect(html2Md("<b><i>abc</i></b>")).toBe('abc')
  })


  it('强制修改config为当前提供的值，只消除i',()=>{
    expect(html2Md("<b><i>abc</i></b>",{emptyTags:['i']},true)).toBe('**abc**')
  })
})
