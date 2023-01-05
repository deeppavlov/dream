> 一个用于转换`HTML`为`Markdown`的工具。[English](./README-EN.md)

---

[![Build Status](https://travis-ci.org/stonehank/html-to-md.svg?branch=master)](https://travis-ci.org/stonehank/html-to-md)
[![npm](https://img.shields.io/npm/v/html-to-md.svg)](https://www.npmjs.com/package/html-to-md)
[![codecov](https://codecov.io/gh/stonehank/html-to-md/branch/master/graph/badge.svg)](https://codecov.io/gh/stonehank/html-to-md)
![npm bundle size](https://img.shields.io/bundlephobia/minzip/html-to-md.svg)
![](https://img.shields.io/badge/dependencies-0-brightgreen)

### 特点

- 快速，小巧，无任何依赖，`gzip` 10kb

- 支持`nodeJS`，参数(html 文本)为字符串

- 200+单元测试和模块测试，覆盖率`97%`

> 注意：只有有效规范的 HTML 文本才能准确显示结果，如`<p>abc<` ，`<i>abc</>`等都是**无效**文本

### 效果

[live-demo](https://stonehank.github.io/html-to-md/)

### 为什么做这个工具

最初的动机是希望将`leetcode-cn`上的题目和自己的解答[搬到`github`](https://github.com/stonehank/leetcode-solution-js)，
但是获取的介绍都是`html`格式文本，因此有了将`html`转换为`markdown`的需求。

找了几个工具，结果并不是很合胃口，有的不支持`nodejs`，有的并不能很好的转换，最终决定自己写一个来用。

刚开始只是写了一个比较简单的，但已经能够处理我的需求。

但后来偶尔一次使用，面对更复杂的`html`格式，就会出现混乱，这个库也就是一个重构版，
当然，它可能还存在很多`bug`没有发现，但希望能在后续不断完善，如果有发现`bug`，请提`issue`或`PR`，我会第一时间进行处理。

### 使用说明

##### 安装

`npm -i html-to-md`

##### 使用

```js
const html2md = require('html-to-md')
// or if you're using ES6
import html2md from 'html-to-md'

console.log(
  html2md('<strong><em>strong and italic</em></strong>', options, force)
)
// ***strong and italic***
```

### 参数(可选)：

#### options:

<table>
<thead>
<tr>
<th align="center">名称</th>
<th align="center">数据类型</th>
<th align="center">默认值</th>
<th align="center">说明</th>
</tr>
</thead>
<tbody>
<tr>
<td align="center">skipTags</td>
<td align="center">Array</td>
<td align="left"><pre>
<code>[
  'div',
  'html',
  'body',
  'nav',
  'section',
  'footer',
  'main',
  'aside',
  'article',
  'header'
]</code></pre></td>
<td align="center">需要忽略的标签名</td>
</tr>
<tr>
<td align="center">emptyTags</td>
<td align="center">Array</td>
<td align="center"><code>[]</code></td>
<td align="center">不仅忽略它本身，它内部所有标签名全部忽略</td>
</tr>
<tr>
<td align="center">ignoreTags</td>
<td align="center">Array</td>
<td align="left">
<pre>
<code>[
  '',
  'style',
  'head',
  '!doctype',
  'form',
  'svg',
  'noscript',
  'script',
  'meta'
]</code></pre></td>
<td align="center">忽视标签及其内部所有内容</td>
</tr>
<tr>
<td align="center">aliasTags</td>
<td align="center">Object</td>
<td align="left">
  <pre>
<code>{
  figure :'p',
  figcaption:'p',
  dl:'p', 
  dd:'p', 
  dt:'p'
}</code></pre></td>
<td align="center">为标签定义一个别名(通常作用于一些不常用标签)</td>
</tr>
<tr>
<td align="center">renderCustomTags</td>
<td align="left">&nbsp;&nbsp;<code>Boolean</code> <br>| <code>'SKIP'</code> <br>| <code>'EMPTY'</code> <br>| <code>'IGNORE'</code></td>
<td align="center">
<code>true</code></td>
<td align="left">自定义当前标签部分属性配置</td>
</tr>
<tr>
<td align="center">tagListener</td>
<td align="left">Function</td>
<td align="center">
(props: <a href="#TagListenerProps">TagListenerProps</a>): <a href="#TagListenerReturnProps">TagListenerReturnProps</a> => props
</td>
<td align="left">定义是否渲染自定义标签（非HTML标签），
<ul>
<li><code>true</code>：渲染</li>
<li><code>false | SKIP</code>：添加至<code>skipTags</code></li>
<li><code>EMPTY</code>：添加至<code>emptyTags</code></li>
<li><code>IGNORE</code>：添加至<code>ignoreTags</code></li>
</ul>
</td>
</tr>
</tbody>
</table>

> 优先权：skipTags > emptyTags > ignoreTags > aliasTags

例：

```javascript
html2md('<><b><i>abc</i></b></>', { ignoreTags: [''] })
// ''

html2md('<><b><i>abc</i></b></>', { skipTags: [''] })
// ***abc***

html2md('<><b><i>abc</i></b></>', { emptyTags: [''] })
// abc

html2md('<><b><i>abc</i></b></>', {
  skipTags: [''],
  aliasTags: { b: 'ul', i: 'li' },
})
// *  abc

html2md('<test><b><i>abc</i></b></test>', { renderCustomTags: 'SKIP' })
// ***abc***
```

#### force(Boolean)(默认 false)

|  值   |                说明                 |
| :---: | :---------------------------------: |
| true  |       表示强制使用自定义配置        |
| false | 对自定义配置使用`Object.assign`操作 |

例：

```javascript
// 默认 skipTags 为 ['div','html','body']

// 配置一：
html2md('<div><b><i>abc</i></b></div>', { skipTags: ['b'] }, false)
// skipTags 为 ['div','html','body','b']

// 配置二：
html2md('<div><b><i>abc</i></b></div>', { skipTags: ['b'] }, true)
// 经过配置后 skipTags 为 ['b']
```

#### TagListenerProps

|key|说明|
|---|---|
|parentTag|父标签名，没有则为null|
|prevTagName|上一个标签名，没有则为null|
|nextTagName|下一个标签名，没有则为null|
|isFirstSubTag|是否当前父标签内部的第一个子标签|
|attrs|当前标签的attributes，以object集合方式，例如 { src, href ... }|
|innerHTML|内部HTML字符串|
|match|当前的HTML对应Markdown的匹配符号|
|language?|当前标签语言，只在 pre 标签中出现 |
|isSelfClosing|是否自闭和标签|



#### TagListenerReturnProps

|key|说明|
|---|---|
|attrs|当前标签的attributes，以object集合方式，例如 { src, href ... }|
|match|返回一个新的自定义匹配符号|
|language?|返回自定义pre标签的language |



### 支持标签

- `a`
- `b`
- `blockquote`
- `code`
- `del`
- `em`
- `h1~h6`
- `hr`
- `i`
- `img`
- `input`
- `li`
- `ol`
- `p`
- `pre`
- `s`
- `strong`
- `table`
- `tbody`
- `td`
- `th`
- `thead`
- `tr`
- `ul`
