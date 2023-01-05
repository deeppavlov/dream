// import B from '../../src/tags/b'
import html2Md from '../../src/index'
import {SYMBOL_I,SYMBOL_B} from '../options'

describe("test <b></b> tag",()=>{
  it('no nest',()=>{
    let b=html2Md("<b>b</b>")
    expect(b).toBe(SYMBOL_B+"b"+SYMBOL_B)
  })

  it('can nest',()=>{
    let b=html2Md("<b><i>b and italic</i></b>")
    expect(b).toBe("***b and italic***")
  })

  it('换行需要省略',()=>{
    let b=html2Md("<b>\n" +
      "<i>b and italic</i>\n" +
      "</b>")
    expect(b).toBe("***b and italic***")
  })
})
