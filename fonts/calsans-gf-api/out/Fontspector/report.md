## FontSpector report

fontspector version: 1.7.1






## Check results




<details><summary>[3] </summary>
<div>


<details>
    <summary>⚠️ <b>WARN</b> Check for codepoints not covered by METADATA subsets. (googlefonts/metadata/unreachable_subsetting)</summary>
    <div>








- ⚠️ **WARN** CalSans-Italic[GEOM,SHRP,YTAS,opsz,wght].ttf: The following codepoints supported by the font are not covered by any subsets defined in the font's metadata file, and will never be served. You can solve this by either manually adding additional subset declarations to METADATA.pb, or by editing the glyphset definitions.

* U+02D8 BREVE: try adding one of: canadian-aboriginal, yi
* U+02D9 DOT ABOVE: try adding one of: canadian-aboriginal, yi
* U+02DB OGONEK: try adding one of: yi, canadian-aboriginal
* U+0302 COMBINING CIRCUMFLEX ACCENT: try adding one of: cherokee, math, tifinagh, coptic
* U+0306 COMBINING BREVE: try adding one of: tifinagh, old-permic
* U+0307 COMBINING DOT ABOVE: try adding one of: math, coptic, old-permic, duployan, canadian-aboriginal, syriac, malayalam, tifinagh, hebrew, tai-le, todhri
* U+030A COMBINING RING ABOVE: try adding one of: duployan, syriac
* U+030B COMBINING DOUBLE ACUTE ACCENT: try adding one of: cherokee, osage
* U+030C COMBINING CARON: try adding one of: cherokee, tai-le
... and 131 others

Or you can add the above codepoints to one of the subsets supported by the font: cyrillic-ext, latin-ext, latin, vietnamese [code: unreachable-subsetting]
  
  


- ⚠️ **WARN** CalSans[GEOM,SHRP,YTAS,opsz,wght].ttf: The following codepoints supported by the font are not covered by any subsets defined in the font's metadata file, and will never be served. You can solve this by either manually adding additional subset declarations to METADATA.pb, or by editing the glyphset definitions.

* U+02D8 BREVE: try adding one of: canadian-aboriginal, yi
* U+02D9 DOT ABOVE: try adding one of: canadian-aboriginal, yi
* U+02DB OGONEK: try adding one of: yi, canadian-aboriginal
* U+0302 COMBINING CIRCUMFLEX ACCENT: try adding one of: cherokee, math, tifinagh, coptic
* U+0306 COMBINING BREVE: try adding one of: tifinagh, old-permic
* U+0307 COMBINING DOT ABOVE: try adding one of: math, coptic, old-permic, duployan, canadian-aboriginal, syriac, malayalam, tifinagh, hebrew, tai-le, todhri
* U+030A COMBINING RING ABOVE: try adding one of: duployan, syriac
* U+030B COMBINING DOUBLE ACUTE ACCENT: try adding one of: cherokee, osage
* U+030C COMBINING CARON: try adding one of: cherokee, tai-le
... and 131 others

Or you can add the above codepoints to one of the subsets supported by the font: cyrillic-ext, latin-ext, latin, vietnamese [code: unreachable-subsetting]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Check for presence of an ARTICLE.en_us.html file (googlefonts/description/has_article)</summary>
    <div>








- ℹ️ **INFO** This font doesn't have an ARTICLE.en_us.html file. [code: missing-article]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Check axis ordering on the STAT table. (googlefonts/STAT/axis_order)</summary>
    <div>








- ℹ️ **INFO** None of the fonts lack a STAT table.

	And these are the most common STAT axis orderings:
	opsz-GEOM-wght-YTAS-SHRP-ital: 2 [code: summary]
  
  

</div>
</details>


</div>
</details>


<details><summary>[14] CalSans-Italic[GEOM,SHRP,YTAS,opsz,wght].ttf</summary>
<div>


<details>
    <summary>🔥 <b>FAIL</b> 
    Validate defaults on fvar table match registered fallback names in GFAxisRegistry.
     (googlefonts/axisregistry/fvar_axis_defaults)</summary>
    <div>








- 🔥 **FAIL** The defaul value YTAS:720 is not registered as an axis fallback name on the Google Axis Registry.
	You should consider suggesting the addition of this value to the registry or adopted one of the existing fallback names for this axis:
	750 [code: not-registered]
  
  

</div>
</details>





<details>
    <summary>🔥 <b>FAIL</b> 
    Validate STAT particle names and values match the fallback names in GFAxisRegistry.
     (googlefonts/STAT/axisregistry)</summary>
    <div>








- 🔥 **FAIL** Axis Value for 'YTAS':'Normal' is expected to be '750' but this font has '720'. [code: bad-coordinate]
  
  

</div>
</details>





<details>
    <summary>⚠️ <b>WARN</b> Check if each glyph has the recommended amount of contours. (contour_count)</summary>
    <div>








- ⚠️ **WARN** This check inspects the glyph outlines and detects the total number of contours in each of them. The expected values are
     inferred from the typical amounts of contours observed in a
     large collection of reference font families. The divergences
     listed below may simply indicate a significantly different
     design on some of your glyphs. On the other hand, some of these
     may flag actual bugs in the font such as glyphs mapped to an
     incorrect codepoint. Please consider reviewing the design and
     codepoint assignment of these to make sure they are correct.


    The following glyphs do not have the recommended number of contours:
* Ibreve (U+012C): found 4, expected one of: [2, 3, 6]
* Idotaccent (U+0130): found 4, expected one of: [2, 3, 6]
* uni1ECA (U+1ECA): found 4, expected one of: [2, 3, 6]
* uni1EC8 (U+1EC8): found 4, expected one of: [2, 3, 6]
* Imacron (U+012A): found 4, expected one of: [2, 3, 6]
* Itilde (U+0128): found 4, expected one of: [2, 3, 6]
* uni01E3 (U+01E3): found 2, expected one of: [3, 4, 5]
* uni0E3F.tf (unencoded): found 5, expected one of: [3]
* uni2612 (U+2612): found 4, expected one of: [3, 5, 6]
... and 12 others [code: contour-count]
  
  

</div>
</details>





<details>
    <summary>⚠️ <b>WARN</b> Ensure variable fonts have relatively consistent sidebearings. (suspicious_sidebearings)</summary>
    <div>








- ⚠️ **WARN** Glyph "uni2006" has suspiciously high variation (z-score 15.67) in right sidebearings at locations:
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=100.00 [code: large-rsb-variation]
  
  


- ⚠️ **WARN** Glyph "uni2005" has suspiciously high variation (z-score 12.16) in right sidebearings at locations:
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=100.00 [code: large-rsb-variation]
  
  


- ⚠️ **WARN** Glyph "uni202F" has suspiciously high variation (z-score 15.92) in right sidebearings at locations:
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=8.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=8.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=8.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=100.00 [code: large-rsb-variation]
  
  


- ⚠️ **WARN** Glyph "integral" has suspiciously high variation (z-score 10.44) in right sidebearings at locations:
    opsz=14.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00 [code: large-rsb-variation]
  
  


- ⚠️ **WARN** Glyph "uni202F" has suspiciously high variation (z-score 10.76) in advance widths at locations:
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=100.00 [code: large-aw-variation]
  
  


- ⚠️ **WARN** Glyph "integral" has suspiciously high variation (z-score 30.19) in advance widths at locations:
    opsz=14.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00 [code: large-aw-variation]
  
  


- ⚠️ **WARN** Glyph "uni2006" has suspiciously high variation (z-score 10.76) in advance widths at locations:
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=100.00 [code: large-aw-variation]
  
  


- ⚠️ **WARN** Glyph "k" has suspiciously high variation (z-score 10.03) in advance widths at locations:
    opsz=14.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00 [code: large-aw-variation]
  
  

</div>
</details>





<details>
    <summary>⚠️ <b>WARN</b> Shapes languages in all GF glyphsets. (googlefonts/glyphsets/shape_languages)</summary>
    <div>








- ⚠️ **WARN** Warning language shaping:

| Message                                                           | Languages           |
|-------------------------------------------------------------------|---------------------|
| Auxiliary orthography codepoints:                                 | * fi_Latn (Finnish) |
|   The following auxiliary characters are missing from the font: Ǥ |                     |
|   The following auxiliary characters are missing from the font: Ʒ |                     |
|   The following auxiliary characters are missing from the font: Ǯ |                     |
|   The following auxiliary characters are missing from the font: ǥ |                     |
|   The following auxiliary characters are missing from the font: ʒ |                     |
|   The following auxiliary characters are missing from the font: ǯ |                     | [code: warning-language-shaping]
  
  

</div>
</details>





<details>
    <summary>⚠️ <b>WARN</b> Check variable font instances (googlefonts/fvar_instances)</summary>
    <div>








- ⚠️ **WARN** fvar instance coordinates for non-wght axes are not the same as the fvar defaults. This may be intentional so please check with the font author:

| Name            | current                                      | expected                                    |
|-----------------|----------------------------------------------|---------------------------------------------|
| Italic          | GEOM=50, SHRP=0, YTAS=720, opsz=14, wght=400 | GEOM=0, SHRP=0, YTAS=720, opsz=14, wght=400 |
| Medium Italic   | GEOM=50, SHRP=0, YTAS=720, opsz=14, wght=500 | GEOM=0, SHRP=0, YTAS=720, opsz=14, wght=500 |
| SemiBold Italic | GEOM=50, SHRP=0, YTAS=720, opsz=14, wght=600 | GEOM=0, SHRP=0, YTAS=720, opsz=14, wght=600 |
| Bold Italic     | GEOM=50, SHRP=0, YTAS=720, opsz=14, wght=700 | GEOM=0, SHRP=0, YTAS=720, opsz=14, wght=700 |

 [code: suspicious-fvar-coords]
  
  

</div>
</details>





<details>
    <summary>⚠️ <b>WARN</b> Checking OS/2 achVendID. (googlefonts/vendor_id)</summary>
    <div>








- ⚠️ **WARN** OS/2 VendorID value 'WORD' is not yet recognized.
If you registered it recently, then it's safe to ignore this warning message. Otherwise, you should set it to your own unique 4 character code, and register it with Microsoft at https://www.microsoft.com/typography/links/vendorlist.aspx
 [code: unknown]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Checking OS/2 fsSelection value. (opentype/xavgcharwidth)</summary>
    <div>








- ℹ️ **INFO** OS/2 xAvgCharWidth is 1175 but it should be 1174 which corresponds to the average of the widths of all glyphs in the font. These are similar values, which may be a symptom of the slightly different calculation of the xAvgCharWidth value in font editors. There's further discussion on this at https://github.com/fonttools/fontbakery/issues/1622 [code: xAvgCharWidth-close]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Familyname must be unique according to namecheck.fontdata.com (fontdata_namecheck)</summary>
    <div>








- ℹ️ **INFO** The family name "Cal Sans" seems to be already in use.
Please visit http://namecheck.fontdata.com/ for more info. [code: name-collision]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Show hinting filesize impact. (hinting_impact)</summary>
    <div>








- ℹ️ **INFO** Hinting filesize impact:

 |               | CalSans-Italic[GEOM,SHRP,YTAS,opsz,wght].ttf     |
 |:------------- | ---------------:|
 | Dehinted Size | 574936 |
 | Hinted Size   | 574960   |
 | Increase      | 24      |
 | Change        | 0.0 %  | [code: size-impact]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Font contains all required tables? (required_tables)</summary>
    <div>








- ℹ️ **INFO** This font contains the following optional tables:

    loca
    prep
    GPOS
    GSUB
    gasp [code: optional-tables]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Is the Grid-fitting and Scan-conversion Procedure ('gasp') table
set to optimize rendering? (googlefonts/gasp)</summary>
    <div>








- ℹ️ **INFO** These are the ppm ranges declared on the gasp table:

| PPM <= 65535 | - Use grid-fitting                                    |
|              | 	- Use grayscale rendering                            |
|              | 	- Use gridfitting with ClearType symmetric smoothing |
|              | 	- Use smoothing along multiple axes with ClearType®  |
|--------------|-------------------------------------------------------|
 [code: ranges]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Ensure fonts have ScriptLangTags declared on the 'meta' table. (googlefonts/meta/script_lang_tags)</summary>
    <div>








- ℹ️ **INFO** "Latn" [code: dlng-tag]
  
  


- ℹ️ **INFO** "Latn" [code: slng-tag]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Font has old ttfautohint applied? (googlefonts/old_ttfautohint)</summary>
    <div>








- ℹ️ **INFO** Could not detect which version of ttfautohint was used in this font. It is typically specified as a comment in the font version entries of the 'name' table. Such font version strings are currently: Version 2.012, Version 2.012 [code: version-not-detected]
  
  

</div>
</details>


</div>
</details>


<details><summary>[14] CalSans[GEOM,SHRP,YTAS,opsz,wght].ttf</summary>
<div>


<details>
    <summary>🔥 <b>FAIL</b> 
    Validate defaults on fvar table match registered fallback names in GFAxisRegistry.
     (googlefonts/axisregistry/fvar_axis_defaults)</summary>
    <div>








- 🔥 **FAIL** The defaul value YTAS:720 is not registered as an axis fallback name on the Google Axis Registry.
	You should consider suggesting the addition of this value to the registry or adopted one of the existing fallback names for this axis:
	750 [code: not-registered]
  
  

</div>
</details>





<details>
    <summary>🔥 <b>FAIL</b> 
    Validate STAT particle names and values match the fallback names in GFAxisRegistry.
     (googlefonts/STAT/axisregistry)</summary>
    <div>








- 🔥 **FAIL** Axis Value for 'YTAS':'Normal' is expected to be '750' but this font has '720'. [code: bad-coordinate]
  
  

</div>
</details>





<details>
    <summary>⚠️ <b>WARN</b> Check if each glyph has the recommended amount of contours. (contour_count)</summary>
    <div>








- ⚠️ **WARN** This check inspects the glyph outlines and detects the total number of contours in each of them. The expected values are
     inferred from the typical amounts of contours observed in a
     large collection of reference font families. The divergences
     listed below may simply indicate a significantly different
     design on some of your glyphs. On the other hand, some of these
     may flag actual bugs in the font such as glyphs mapped to an
     incorrect codepoint. Please consider reviewing the design and
     codepoint assignment of these to make sure they are correct.


    The following glyphs do not have the recommended number of contours:
* Ibreve (U+012C): found 4, expected one of: [2, 3, 6]
* Idotaccent (U+0130): found 4, expected one of: [2, 3, 6]
* uni1ECA (U+1ECA): found 4, expected one of: [2, 3, 6]
* uni1EC8 (U+1EC8): found 4, expected one of: [2, 3, 6]
* Imacron (U+012A): found 4, expected one of: [2, 3, 6]
* Itilde (U+0128): found 4, expected one of: [2, 3, 6]
* uni01E3 (U+01E3): found 2, expected one of: [3, 4, 5]
* uni0E3F.tf (unencoded): found 5, expected one of: [3]
* uni2612 (U+2612): found 4, expected one of: [3, 5, 6]
... and 12 others [code: contour-count]
  
  

</div>
</details>





<details>
    <summary>⚠️ <b>WARN</b> Ensure variable fonts have relatively consistent sidebearings. (suspicious_sidebearings)</summary>
    <div>








- ⚠️ **WARN** Glyph "uni202F" has suspiciously high variation (z-score 16.07) in right sidebearings at locations:
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=100.00 [code: large-rsb-variation]
  
  


- ⚠️ **WARN** Glyph "uni2006" has suspiciously high variation (z-score 15.88) in right sidebearings at locations:
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=100.00 [code: large-rsb-variation]
  
  


- ⚠️ **WARN** Glyph "uni2005" has suspiciously high variation (z-score 12.32) in right sidebearings at locations:
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=8.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=513.66, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=100.00 [code: large-rsb-variation]
  
  


- ⚠️ **WARN** Glyph "integral" has suspiciously high variation (z-score 32.70) in right sidebearings at locations:
    opsz=14.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00 [code: large-rsb-variation]
  
  


- ⚠️ **WARN** Glyph "eth" has suspiciously high variation (z-score 15.86) in advance widths at locations:
    opsz=14.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00 [code: large-aw-variation]
  
  


- ⚠️ **WARN** Glyph "uni202F" has suspiciously high variation (z-score 10.77) in advance widths at locations:
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=100.00 [code: large-aw-variation]
  
  


- ⚠️ **WARN** Glyph "uni2006" has suspiciously high variation (z-score 10.77) in advance widths at locations:
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=0.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=50.00, wght=700.00, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=585.62, YTAS=800.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=720.00, SHRP=100.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=0.00
    opsz=48.00, GEOM=100.00, wght=700.00, YTAS=800.00, SHRP=100.00 [code: large-aw-variation]
  
  


- ⚠️ **WARN** Glyph "integral" has suspiciously high variation (z-score 28.58) in advance widths at locations:
    opsz=14.00, GEOM=0.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=50.00, wght=400.00, YTAS=800.00, SHRP=0.00
    opsz=14.00, GEOM=100.00, wght=400.00, YTAS=800.00, SHRP=0.00 [code: large-aw-variation]
  
  

</div>
</details>





<details>
    <summary>⚠️ <b>WARN</b> Shapes languages in all GF glyphsets. (googlefonts/glyphsets/shape_languages)</summary>
    <div>








- ⚠️ **WARN** Warning language shaping:

| Message                                                           | Languages           |
|-------------------------------------------------------------------|---------------------|
| Auxiliary orthography codepoints:                                 | * fi_Latn (Finnish) |
|   The following auxiliary characters are missing from the font: Ǥ |                     |
|   The following auxiliary characters are missing from the font: Ʒ |                     |
|   The following auxiliary characters are missing from the font: Ǯ |                     |
|   The following auxiliary characters are missing from the font: ǥ |                     |
|   The following auxiliary characters are missing from the font: ʒ |                     |
|   The following auxiliary characters are missing from the font: ǯ |                     | [code: warning-language-shaping]
  
  

</div>
</details>





<details>
    <summary>⚠️ <b>WARN</b> Check variable font instances (googlefonts/fvar_instances)</summary>
    <div>








- ⚠️ **WARN** fvar instance coordinates for non-wght axes are not the same as the fvar defaults. This may be intentional so please check with the font author:

| Name     | current                                      | expected                                    |
|----------|----------------------------------------------|---------------------------------------------|
| Regular  | GEOM=50, SHRP=0, YTAS=720, opsz=14, wght=400 | GEOM=0, SHRP=0, YTAS=720, opsz=14, wght=400 |
| Medium   | GEOM=50, SHRP=0, YTAS=720, opsz=14, wght=500 | GEOM=0, SHRP=0, YTAS=720, opsz=14, wght=500 |
| SemiBold | GEOM=50, SHRP=0, YTAS=720, opsz=14, wght=600 | GEOM=0, SHRP=0, YTAS=720, opsz=14, wght=600 |
| Bold     | GEOM=50, SHRP=0, YTAS=720, opsz=14, wght=700 | GEOM=0, SHRP=0, YTAS=720, opsz=14, wght=700 |

 [code: suspicious-fvar-coords]
  
  

</div>
</details>





<details>
    <summary>⚠️ <b>WARN</b> Checking OS/2 achVendID. (googlefonts/vendor_id)</summary>
    <div>








- ⚠️ **WARN** OS/2 VendorID value 'WORD' is not yet recognized.
If you registered it recently, then it's safe to ignore this warning message. Otherwise, you should set it to your own unique 4 character code, and register it with Microsoft at https://www.microsoft.com/typography/links/vendorlist.aspx
 [code: unknown]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Checking OS/2 fsSelection value. (opentype/xavgcharwidth)</summary>
    <div>








- ℹ️ **INFO** OS/2 xAvgCharWidth is 1176 but it should be 1175 which corresponds to the average of the widths of all glyphs in the font. These are similar values, which may be a symptom of the slightly different calculation of the xAvgCharWidth value in font editors. There's further discussion on this at https://github.com/fonttools/fontbakery/issues/1622 [code: xAvgCharWidth-close]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Familyname must be unique according to namecheck.fontdata.com (fontdata_namecheck)</summary>
    <div>








- ℹ️ **INFO** The family name "Cal Sans" seems to be already in use.
Please visit http://namecheck.fontdata.com/ for more info. [code: name-collision]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Show hinting filesize impact. (hinting_impact)</summary>
    <div>








- ℹ️ **INFO** Hinting filesize impact:

 |               | CalSans[GEOM,SHRP,YTAS,opsz,wght].ttf     |
 |:------------- | ---------------:|
 | Dehinted Size | 543636 |
 | Hinted Size   | 543660   |
 | Increase      | 24      |
 | Change        | 0.0 %  | [code: size-impact]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Font contains all required tables? (required_tables)</summary>
    <div>








- ℹ️ **INFO** This font contains the following optional tables:

    loca
    prep
    GPOS
    GSUB
    gasp [code: optional-tables]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Is the Grid-fitting and Scan-conversion Procedure ('gasp') table
set to optimize rendering? (googlefonts/gasp)</summary>
    <div>








- ℹ️ **INFO** These are the ppm ranges declared on the gasp table:

| PPM <= 65535 | - Use grid-fitting                                    |
|              | 	- Use grayscale rendering                            |
|              | 	- Use gridfitting with ClearType symmetric smoothing |
|              | 	- Use smoothing along multiple axes with ClearType®  |
|--------------|-------------------------------------------------------|
 [code: ranges]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Ensure fonts have ScriptLangTags declared on the 'meta' table. (googlefonts/meta/script_lang_tags)</summary>
    <div>








- ℹ️ **INFO** "Latn" [code: dlng-tag]
  
  


- ℹ️ **INFO** "Latn" [code: slng-tag]
  
  

</div>
</details>





<details>
    <summary>ℹ️ <b>INFO</b> Font has old ttfautohint applied? (googlefonts/old_ttfautohint)</summary>
    <div>








- ℹ️ **INFO** Could not detect which version of ttfautohint was used in this font. It is typically specified as a comment in the font version entries of the 'name' table. Such font version strings are currently: Version 2.012, Version 2.012 [code: version-not-detected]
  
  

</div>
</details>


</div>
</details>






### Summary

| 🔥 FAIL | ⚠️ WARN | ℹ️ INFO | ✅ PASS | ⏩ SKIP | 
| ---|---|---|---|---|
| 4 | 26 | 18 | 246 | 83 | 
| 1% | 7% | 5% | 69% | 23% | 



