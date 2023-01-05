import Li from '../../src/tags/li'


describe('test <li></li> tag',()=>{
  it('no nest',()=>{
    let li=new Li("<li>javascript</li>")
    expect(li.exec()).toBe("\n" +
      "* javascript\n")
  })

  it('can nest',()=>{
    let li=new Li("<li><strong>strong</strong></li>")
    expect(li.exec()).toBe("\n* **strong**\n")
  })
})
