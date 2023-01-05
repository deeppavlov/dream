import html2Md from '../../src/index'


describe('直接忽视整个tag',()=>{


  it('忽视 所有 ',()=>{
    expect(html2Md("<><b><i>abc</i></b></>",{ignoreTags:['']}, true)).toBe('')
  })


  it('忽视 i 及其内部abc ',()=>{
    expect(html2Md("<b><i>abc</i></b>",{ignoreTags:['i']})).toBe('')
  })

  it('忽视内部所有tag',()=>{
    expect(html2Md("<b><i>abc</i></b>",{ignoreTags:['b']})).toBe('')
  })


  it('忽视自闭和标签',()=>{
    expect(html2Md("<br><del>delete</del>",{ignoreTags:['br']})).toBe('~~delete~~')
    expect(html2Md("<br/><del>delete</del>",{ignoreTags:['br']})).toBe('~~delete~~')
  })
})
