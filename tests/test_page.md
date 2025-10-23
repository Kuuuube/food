# Markdown syntax guide

## Headers

# This is a Heading h1
## This is a Heading h2

### This is a Heading h3

#### This is a Heading h4

##### This is a Heading h5
###### This is a Heading h6

-# This is a subtext

## Emphasis

*This text will be italic*  
_This will also be italic_

**This text will be bold**  

_You **can** combine them this way_
*and **this** way*

__This will be underlined__

## Lists

### Unordered

* Item 1
* Item 2
* Item 2a
* Item 2b
    * Item 3a
    * Item 3b

### Ordered

1. Item 1
2. Item 2
3. Item 3
    1. Item 3a
    2. Item 3b

<!-- -->

1. 1
2. 2
3. 3
4. 4
5. 5
6. 6
7. 7
8. 8
9. 9
10. 10
11. 11
12. 12
13. 13
14. 14
15. 15

## Links

This is a link to [Kuuuube's github profile](https://github.com/Kuuuube).

## Blockquotes

> Markdown is a lightweight markup language with plain-text-formatting syntax, created in 2004 by John Gruber with Aaron Swartz.

>>> Markdown is often used to format readme files, for writing messages in online discussion forums, and to create rich text using a plain text editor.
If you use three greater than symbols instead of just one it will pull in the next line
and the next line
and as many lines as you want

as long as you dont put a blank newline inbetween them

## Tables

| Left columns  | Right columns |
| ------------- |:-------------:|
| left foo      | right foo     |
| left bar      | right bar     |
| left baz      | right baz     |

## Blocks of code

```
let message = 'Hello world';
alert(message);
```

## Inline code

This page site is rendered using `Kuuuube's custom markdown renderer`.

`inline code on another line over here` and some other stuff

## Inline HTML Test

Some text with an extra line break below it:

<br>

Text after this line break.

</br>

The above line break uses the auto closing tag but the previous one didn't. They both render identically.
