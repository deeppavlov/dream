import Hr from '../../src/tags/hr'

describe('test <hr></hr> tag',()=>{
  it('self-close',()=>{
    let hr=new Hr("<hr />")
    expect(hr.exec()).toBe("\n---\n")
  })
})
