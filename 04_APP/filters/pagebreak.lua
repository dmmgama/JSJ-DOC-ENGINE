-- filters/pagebreak.lua
-- Lua filter para Pandoc.
-- Interpreta marcadores de paginação injectados pelo compile.py
-- e converte em Raw OpenXML para DOCX.

local function is_pagebreak(el)
  return el.text and el.text:match("^%s*<!%-%-%s*pagebreak%s*%-%->%s*$")
end

local function is_sectionbreak(el)
  return el.text and el.text:match("^%s*<!%-%-%s*sectionbreak%s*%-%->%s*$")
end

local function is_sectionbreak_landscape(el)
  return el.text and el.text:match("^%s*<!%-%-%s*sectionbreak%-landscape%s*%-%->%s*$")
end

local PAGE_BREAK_XML = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'

local SECTION_BREAK_XML = '<w:p><w:pPr><w:sectPr><w:type w:val="nextPage"/></w:sectPr></w:pPr></w:p>'

local SECTION_BREAK_LANDSCAPE_XML = [[
<w:p><w:pPr><w:sectPr>
  <w:type w:val="nextPage"/>
  <w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>
</w:sectPr></w:pPr></w:p>]]

function RawBlock(el)
  if el.format == "html" then
    if is_pagebreak(el) then
      return pandoc.RawBlock("openxml", PAGE_BREAK_XML)
    elseif is_sectionbreak_landscape(el) then
      return pandoc.RawBlock("openxml", SECTION_BREAK_LANDSCAPE_XML)
    elseif is_sectionbreak(el) then
      return pandoc.RawBlock("openxml", SECTION_BREAK_XML)
    end
  end
end
