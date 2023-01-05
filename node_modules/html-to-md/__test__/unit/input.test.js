import Input from '../../src/tags/input'
import Li from '../../src/tags/li'


describe('test <input /> tag',()=>{
  it('render alone, should do nothing',()=>{
    let input=new Input("<input type='checkbox' disabled checked/>")
    expect(input.exec()).toBe("")
  })

  it('parent tag is li, should be parsed(checked)',()=>{
    let li=new Li("<li><input type='checkbox' disabled checked/>checked</li>")
    expect(li.exec()).toBe("\n* [x] checked\n")
  })

  it('parent tag is li, should be parsed(no checked)',()=>{
    let li=new Li('<li><input type="checkbox" disabled />not checked</li>')
    expect(li.exec()).toBe("\n* [ ] not checked\n")
  })

  it('parent tag is li, but is not checkbox, do nothing)',()=>{
    let li=new Li('<li><input type="text" disabled />text</li>')
    expect(li.exec()).toBe('\n' +
      '* text\n')
  })

  // it('parent tag is li, but checkbox is not disabled, do nothing)',()=>{
  //   let li=new Li('<li><input type="checkbox" checked >not disabled</li>')
  //   expect(li.exec()).toBe('\n' +
  //     '* <input type="checkbox" checked >not disabled\n')
  // })

  it('parent tag is li, but checkbox is not disabled, will auto convert to disable)',()=>{
    let li=new Li('<li><input type="checkbox" checked >not disabled</li>')
    expect(li.exec()).toBe("\n" +
      "* [x] not disabled\n")
  })


})
