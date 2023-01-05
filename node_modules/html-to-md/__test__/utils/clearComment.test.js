import html2Md from '../../src/index'

describe('清空注释',()=>{

  it('清除注释1',()=>{
    expect(html2Md('<b><!--This is Comment -->strong</b>')).toBe("**strong**")
  })

  it('清除注释2',()=>{
    expect(html2Md('<b>' +
      '<!--This \n\t' +
      'is \n' +
      'Comment 1\n' +
      '-->strong<!--This \n' +
      'is <b>comment strong</b>\n' +
      'Comment 1\n' +
      '--></b>')).toBe("**strong**")
  })

  it('注释存在 \n \t都省略',()=>{
    expect(html2Md(`<b><!-- This    
	is 
Comment 1   
-->strong
<!--This 
is <b>
comment strong

</b>

Comment 1
--></b>`)).toBe('**strong**')
  })

})
