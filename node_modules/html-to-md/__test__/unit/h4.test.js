import H4 from '../../src/tags/h4'


describe('test <h4></h4> tag',()=>{
  it('no nest',()=>{
    let h4=new H4("<h4>javascript</h4>")
    expect(h4.exec()).toBe("\n#### javascript\n")
  })

  it('can nest',()=>{
    let h4=new H4("<h4><strong><i>strong and italic</i></strong></h4>")
    expect(h4.exec()).toBe("\n#### ***strong and italic***\n")
  })

  it('can nest-2',()=>{
    let h4=new H4("<h4 class=\"line\" data-line=\"174\"><a href=\"https://github.com/markdown-it/markdown-it-sub\">Subscript</a> / <a href=\"https://github.com/markdown-it/markdown-it-sup\">Superscript</a></h4>")
    expect(h4.exec()).toBe("\n" +
      "#### [Subscript](https://github.com/markdown-it/markdown-it-sub) / [Superscript](https://github.com/markdown-it/markdown-it-sup)\n")
  })
})
