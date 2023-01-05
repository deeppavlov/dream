import html2Md from '../../src/index'

describe('对于不匹配，消除attrs，标签不处理',()=>{


  it('不匹配消除attrs',()=>{
    expect(html2Md("<notmatch onclick='alert(1)'><i>abc</i></notmatch>", { renderCustomTags: true })).toBe('<notmatch>*abc*</notmatch>')
  })

  it('自闭和标签，不匹配消除attrs',()=>{
    expect(html2Md('<notmatch onclick="alert(1)"><i><source data-id="xxx" style="width:5rem"/></i></notmatch>', { renderCustomTags: true })).toBe('<notmatch>*<source />*</notmatch>')
  })

})
