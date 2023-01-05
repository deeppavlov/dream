import H6 from '../../src/tags/h6'

describe('test <h6></h6> tag',()=>{
  it('no nest',()=>{
    let h6=new H6("<h6>javascript</h6>")
    expect(h6.exec()).toBe("\n###### javascript\n")
  })

  it('can nest',()=>{
    let h6=new H6("<h6><strong><i>strong and italic</i></strong></h6>")
    expect(h6.exec()).toBe("\n###### ***strong and italic***\n")
  })

  it('can nest-2',()=>{
    let h6=new H6("<h6 class=\"line\" data-line=\"174\"><a href=\"https://github.com/markdown-it/markdown-it-sub\">Subscript</a> / <a href=\"https://github.com/markdown-it/markdown-it-sup\">Superscript</a></h6>")
    expect(h6.exec()).toBe("\n" +
      "###### [Subscript](https://github.com/markdown-it/markdown-it-sub) / [Superscript](https://github.com/markdown-it/markdown-it-sup)\n")
  })
})
