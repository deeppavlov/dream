import html2Md from '../../src/index'

describe('Tag listener',()=>{

  it('tagListener language',()=>{
    expect(html2Md('<pre class="language-tsx"><code>var a = 2</code></pre>', {tagListener:(tagName, props)=>{
      return {
        ...props,
        language: props.language  === 'tsx' ? 'typescript' : 'javascript'
      }
    }})).toBe("```typescript\n" + 
    "var a = 2\n" + 
    "```")
  })
  
  it('tagListener change match symbol',()=>{
    expect(html2Md('<b>Not bold, del instead</b>', {tagListener:(tagName, props)=>{
      return {
        ...props,
        match: props.match === '**' ? '~~' : props.match
      }
    }})).toBe("~~Not bold, del instead~~")
  })
})
