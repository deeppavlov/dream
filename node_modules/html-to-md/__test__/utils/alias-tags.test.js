import html2Md from '../../src/index'

describe('替换标签',()=>{

  it('figure as div',()=>{
    expect(html2Md('<figure>Figure show as div</figure>')).toBe("Figure show as div")
  })

  it('figcaption as p',()=>{
    expect(html2Md(
`<figure>
  <img src="someimg.jpg" alt="" style="width:100%">
  <figcaption>Fig.1 - Trulli, Puglia, Italy.</figcaption>
</figure>`)).toBe("![](someimg.jpg)\n" +
      "\n" +
      "Fig.1 - Trulli, Puglia, Italy.")
  })

  it('No li in ul, but use alias-tag',()=>{
    expect(html2Md(
`<ul>
      <b>this b is alias as li</b>
      <i>this i is alias as li</i>
</ul>`
, {aliasTags: {b: 'li', i:'li'}}))
.toBe(
`* this b is alias as li
* this i is alias as li`
)})

it('No li in ol, but use alias-tag',()=>{
  expect(html2Md(
`<ol>
    <b>this b is alias as li</b>
    <i>this i is alias as li</i>
</ol>`
, {aliasTags: {b: 'li', i:'li'}}))
.toBe(
`1. this b is alias as li
2. this i is alias as li`
)})

})
