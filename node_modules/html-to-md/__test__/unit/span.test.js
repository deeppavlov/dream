import Span from '../../src/tags/span'
import html2Md from '../../src/index'


describe('test <span></span> tag',()=>{
  it('no nest',()=>{
    let span=new Span("<span>javascript</span>")
    expect(span.exec()).toBe("javascript")
  })


  it('code in span will also resolve',()=>{
    let span=new Span("<span><strong>strong</strong></span>")
    expect(span.exec()).toBe("**strong**")
  })

  // it('span will treat as p, but no change line',()=>{
  //   let spanResStr=html2Md("<span><strong>strong</strong></span><span><strong>strong</strong></span>")
  //   expect(spanResStr).toBe("**strongstrong**")
  // })


})
