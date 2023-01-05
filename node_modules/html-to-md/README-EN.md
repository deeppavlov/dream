> A JS library for converting HTML to Markdown.[中文](./README.md)

---

[![Build Status](https://travis-ci.org/stonehank/html-to-md.svg?branch=master)](https://travis-ci.org/stonehank/html-to-md)
[![npm](https://img.shields.io/npm/v/html-to-md.svg)](https://www.npmjs.com/package/html-to-md)
[![codecov](https://codecov.io/gh/stonehank/html-to-md/branch/master/graph/badge.svg)](https://codecov.io/gh/stonehank/html-to-md)
![npm bundle size](https://img.shields.io/bundlephobia/minzip/html-to-md.svg)
![](https://img.shields.io/badge/dependencies-0-brightgreen)

<!-- ![David](https://img.shields.io/david/stonehank/html-to-md.svg) -->

### Feature

- speed, none of dependencies, `gizp` 10kb

- support `nodeJs`

- 200+`unit test` and `module test`, code coverage `97%`

> Only valid HTML will be output correctly, eg. `<p>abc<`, `<i>abc</>` are **Not Valid** text.

### Live Demo

[live-demo](https://stonehank.github.io/html-to-md/)

### Useage

##### install

`npm i html-to-md`

##### example

```js
const html2md = require("html-to-md");
// or if you're using ES6
import html2md from "html-to-md";

console.log(html2md("<strong><em>strong and italic</em></strong>", options));
// ***strong and italic***
```

### Config(Optional)：

#### options:

<table>
<thead>
<tr>
<th align="center">name</th>
<th align="center">date type</th>
<th align="center">default value</th>
<th align="center">description</th>
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
<td align="center">Declare which tags need to skip</td>
</tr>
<tr>
<td align="center">emptyTags</td>
<td align="center">Array</td>
<td align="center"><code>[]</code></td>
<td align="center">Skip all the tags inside it</td>
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
<td align="center"> Ignore all tag and content inside the tag</td>
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
<td align="center"> Define an alias tag name</td>
</tr>
<tr>
<td align="center">renderCustomTags</td>
<td align="left">&nbsp;&nbsp;<code>Boolean</code> <br>| <code>'SKIP'</code> <br>| <code>'EMPTY'</code> <br>| <code>'IGNORE'</code></td>
<td align="center">
<code>true</code></td>
<td align="left">Define how to render not valida HTML tags
<ul>
<li><code>true</code>: render all custom tags</li>
<li><code>false | SKIP</code>: render as <code>skipTags</code></li>
<li><code>EMPTY</code>: render as <code>emptyTags</code></li>
<li><code>IGNORE</code>: render as <code>ignoreTags</code></li>
</ul>
</td>
</tr>
<tr>
<td align="center">tagListener</td>
<td align="left">Function</td>
<td align="center">
(tagName, props: <a href="#TagListenerProps">TagListenerProps</a>): <a href="#TagListenerReturnProps">TagListenerReturnProps</a> => props
</td>
<td align="left">Custom the tag props</td>
</tr>
</tbody>
</table>

> Priority：skipTags > emptyTags > ignoreTags > aliasTags

Example:

```javascript
html2md("<><b><i>abc</i></b></>", { ignoreTags: [""] });
// ''

html2md("<><b><i>abc</i></b></>", { skipTags: [""] });
// ***abc***

html2md("<><b><i>abc</i></b></>", { emptyTags: [""] });
// abc

html2md("<><b><i>abc</i></b></>", {
  skipTags: [""],
  aliasTags: { b: "ul", i: "li" },
});
// *  abc

html2md("<test><b><i>abc</i></b></test>", { renderCustomTags: "SKIP" });
// ***abc***
```

#### force(Boolean)(Default value is false)

| value |                            description                            |
| :---: | :---------------------------------------------------------------: |
| true  |                 Overwrite by your custom options                  |
| false | Use `Object.assign` to combine custom options and default options |

Example：

```javascript
// The default skipTags value is ['div','html','body']

// ex1：
html2md("<div><b><i>abc</i></b></div>", { skipTags: ["b"] }, false);
// skipTags value become ['div','html','body','b']

// ex2：
html2md("<div><b><i>abc</i></b></div>", { skipTags: ["b"] }, true);
// skipTags value become ['b']
```
#### TagListenerProps

|key|说明|
|---|---|
|parentTag|parent tag nam, `null` if not exist|
|prevTagName|previous tag name, `null` if not exist|
|nextTagName|next tag name, `null` if not exist|
|isFirstSubTag|if the current tag is the first tag of its parent tag|
|attrs|tag's attributes, format as object, e.g. `{ src, href ... }`|
|innerHTML|inner html string|
|match|the match symbol of markdown for current tag|
|language?|language for `pre` tag|
|isSelfClosing|is the tag a self-closing tag|



#### TagListenerReturnProps

|key|说明|
|---|---|
|attrs|tag's attributes, format as object, e.g. `{ src, href ... }`|
|match|the match symbol of markdown for current tag|
|language?|language for `pre` tag|


### Support Tags

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
