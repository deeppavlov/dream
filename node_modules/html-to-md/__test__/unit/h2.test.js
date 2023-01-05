import H2 from '../../src/tags/h2'


describe('test <h2></h2> tag',()=>{
  it('no nest',()=>{
    let h2=new H2("<h2>javascript</h2>")
    expect(h2.exec()).toBe("\n## javascript\n")
  })

  it('can nest',()=>{
    let h2=new H2("<h2><strong><i>strong and italic</i></strong></h2>")
    expect(h2.exec()).toBe("\n## ***strong and italic***\n")
  })

  it('can nest-2',()=>{
    let h2=new H2("<h2 class=\"line\" data-line=\"174\"><a href=\"https://github.com/markdown-it/markdown-it-sub\">Subscript</a> / <a href=\"https://github.com/markdown-it/markdown-it-sup\">Superscript</a></h2>")
    expect(h2.exec()).toBe("\n" +
      "## [Subscript](https://github.com/markdown-it/markdown-it-sub) / [Superscript](https://github.com/markdown-it/markdown-it-sup)\n")
  })
})
