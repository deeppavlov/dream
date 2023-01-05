import html2Md from '../../src/index'
import {SYMBOL_I,SYMBOL_B} from '../options'
describe('test <i></i> tag',()=>{
  it('no nest',()=>{
    expect(html2Md("<i>javascript</i>")).toBe(SYMBOL_I+"javascript"+SYMBOL_I)
  })

  it('can nest',()=>{
    expect(html2Md("<i><strong>strong and italic</strong></i>")).toBe(SYMBOL_I+SYMBOL_B+"strong and italic"+SYMBOL_B+SYMBOL_I)
  })
})
