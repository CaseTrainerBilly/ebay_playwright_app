from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from csv_export import calculate_resale_metrics, estimate_buyer_protection_fee, estimate_seller_receives


VISIBLE_COLUMNS = [
    "Image",
    "Title",
    "Price Text",
    "Observed Sold Price",
    "Buyer Protection Fee",
    "Seller Receives",
    "Recommended Max Buy",
    "Expected Profit",
    "ROI",
    "Condition",
    "Sold Date",
    "Shipping",
    "Location",
    "Listing ID",
    "Marketplace",
    "Search Query",
    "Listing URL",
]


def _cell_ref(col_index: int, row_index: int) -> str:
    letters = ""
    index = col_index
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(65 + remainder) + letters
    return f"{letters}{row_index}"


def _inline_string_cell(col_index: int, row_index: int, value: str) -> str:
    ref = _cell_ref(col_index, row_index)
    safe_value = escape(value or "")
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{safe_value}</t></is></c>'


def _number_cell(col_index: int, row_index: int, value: float | int | None) -> str:
    ref = _cell_ref(col_index, row_index)
    if value is None:
        return f'<c r="{ref}"/>'
    return f'<c r="{ref}"><v>{value}</v></c>'


def _money(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def _percent(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value * 100:.0f}%"


def _fetch_image_bytes(image_url: str) -> tuple[bytes, str] | None:
    if not image_url:
        return None

    candidate_urls = [image_url]
    if ".webp" in image_url:
        candidate_urls.append(image_url.replace(".webp", ".jpg"))
        candidate_urls.append(image_url.replace(".webp", ".jpeg"))

    mime_to_ext = {
        "image/jpeg": "jpeg",
        "image/jpg": "jpeg",
        "image/png": "png",
        "image/gif": "gif",
    }

    for candidate_url in candidate_urls:
        try:
            request = Request(candidate_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(request, timeout=10) as response:
                content = response.read()
                content_type = (response.headers.get_content_type() or "").lower()
                extension = mime_to_ext.get(content_type)
                if not extension:
                    if content.startswith(b"\x89PNG\r\n\x1a\n"):
                        extension = "png"
                    elif content[:3] == b"\xff\xd8\xff":
                        extension = "jpeg"
                    elif content[:6] in {b"GIF87a", b"GIF89a"}:
                        extension = "gif"
                if extension:
                    return content, extension
        except Exception:
            continue
    return None


def _drawing_anchor_xml(image_index: int, row_zero_based: int) -> str:
    relationship_id = f"rId{image_index}"
    return f"""
    <xdr:twoCellAnchor editAs="oneCell">
      <xdr:from>
        <xdr:col>0</xdr:col>
        <xdr:colOff>9525</xdr:colOff>
        <xdr:row>{row_zero_based}</xdr:row>
        <xdr:rowOff>9525</xdr:rowOff>
      </xdr:from>
      <xdr:to>
        <xdr:col>1</xdr:col>
        <xdr:colOff>9525</xdr:colOff>
        <xdr:row>{row_zero_based + 1}</xdr:row>
        <xdr:rowOff>9525</xdr:rowOff>
      </xdr:to>
      <xdr:pic>
        <xdr:nvPicPr>
          <xdr:cNvPr id="{image_index}" name="Picture {image_index}"/>
          <xdr:cNvPicPr/>
        </xdr:nvPicPr>
        <xdr:blipFill>
          <a:blip r:embed="{relationship_id}"/>
          <a:stretch><a:fillRect/></a:stretch>
        </xdr:blipFill>
        <xdr:spPr>
          <a:xfrm>
            <a:off x="0" y="0"/>
            <a:ext cx="0" cy="0"/>
          </a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        </xdr:spPr>
      </xdr:pic>
      <xdr:clientData/>
    </xdr:twoCellAnchor>"""


def _worksheet_xml(results: dict, has_images: bool) -> str:
    rows: list[str] = []

    header_cells = [
        _inline_string_cell(col_index, 1, column_name)
        for col_index, column_name in enumerate(VISIBLE_COLUMNS, start=1)
    ]
    rows.append(f'<row r="1" ht="24" customHeight="1">{"".join(header_cells)}</row>')

    resale_metrics = calculate_resale_metrics(results)

    for item_index, item in enumerate(results.get("items", []), start=2):
        sold_price = item.get("price_value")
        marketplace = item.get("marketplace")
        buyer_protection_fee = estimate_buyer_protection_fee(sold_price, marketplace)
        seller_receives = estimate_seller_receives(sold_price, marketplace)

        row_cells = [
            _inline_string_cell(1, item_index, ""),
            _inline_string_cell(2, item_index, item.get("title", "")),
            _inline_string_cell(3, item_index, item.get("price_text", "")),
            _number_cell(4, item_index, sold_price),
            _number_cell(5, item_index, buyer_protection_fee),
            _number_cell(6, item_index, seller_receives),
            _inline_string_cell(7, item_index, ""),
            _inline_string_cell(8, item_index, ""),
            _inline_string_cell(9, item_index, ""),
            _inline_string_cell(10, item_index, item.get("condition", "")),
            _inline_string_cell(11, item_index, item.get("sold_date", "")),
            _inline_string_cell(12, item_index, item.get("shipping_text", "")),
            _inline_string_cell(13, item_index, item.get("location_text", "")),
            _inline_string_cell(14, item_index, item.get("listing_id", "")),
            _inline_string_cell(15, item_index, item.get("marketplace", "")),
            _inline_string_cell(16, item_index, item.get("search_query", "")),
            _inline_string_cell(17, item_index, item.get("url", "")),
        ]
        rows.append(f'<row r="{item_index}" ht="96" customHeight="1">{"".join(row_cells)}</row>')

    summary_row_index = len(results.get("items", [])) + 2
    summary_cells = [
        _inline_string_cell(1, summary_row_index, ""),
        _inline_string_cell(2, summary_row_index, "AVERAGE"),
        _inline_string_cell(3, summary_row_index, ""),
        _number_cell(4, summary_row_index, resale_metrics.get("average_observed_sold_price")),
        _number_cell(5, summary_row_index, resale_metrics.get("average_buyer_protection_fee")),
        _number_cell(6, summary_row_index, resale_metrics.get("average_estimated_sale_price")),
        _number_cell(7, summary_row_index, resale_metrics.get("recommended_max_buy_price")),
        _number_cell(8, summary_row_index, resale_metrics.get("expected_profit_at_max_buy")),
        _inline_string_cell(9, summary_row_index, _percent(resale_metrics.get("roi_at_max_buy"))),
        _inline_string_cell(
            10,
            summary_row_index,
            f"Median {_money(resale_metrics.get('median_estimated_sale_price'))} | Confidence {resale_metrics.get('sell_through_confidence', '')}",
        ),
        _inline_string_cell(11, summary_row_index, ""),
        _inline_string_cell(12, summary_row_index, ""),
        _inline_string_cell(13, summary_row_index, ""),
        _inline_string_cell(14, summary_row_index, ""),
        _inline_string_cell(15, summary_row_index, ""),
        _inline_string_cell(16, summary_row_index, ""),
        _inline_string_cell(17, summary_row_index, ""),
    ]
    rows.append(f'<row r="{summary_row_index}" ht="28" customHeight="1">{"".join(summary_cells)}</row>')

    dimension = f"A1:Q{summary_row_index}"
    drawing_xml = '<drawing r:id="rId1"/>' if has_images else ""
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <dimension ref="{dimension}"/>
  <sheetViews>
    <sheetView workbookViewId="0"/>
  </sheetViews>
  <sheetFormatPr defaultRowHeight="20"/>
  <cols>
    <col min="1" max="1" width="16" customWidth="1"/>
    <col min="2" max="2" width="44" customWidth="1"/>
    <col min="3" max="3" width="14" customWidth="1"/>
    <col min="4" max="8" width="16" customWidth="1"/>
    <col min="9" max="9" width="10" customWidth="1"/>
    <col min="10" max="13" width="16" customWidth="1"/>
    <col min="14" max="16" width="14" customWidth="1"/>
    <col min="17" max="17" width="34" customWidth="1"/>
  </cols>
  <sheetData>
    {''.join(rows)}
  </sheetData>
  {drawing_xml}
</worksheet>'''


def build_xlsx(results: dict) -> bytes:
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    workbook_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <fileVersion appName="xl"/>
  <workbookPr/>
  <bookViews>
    <workbookView xWindow="0" yWindow="0" windowWidth="24000" windowHeight="12000"/>
  </bookViews>
  <sheets>
    <sheet name="Results" sheetId="1" r:id="rId1"/>
  </sheets>
  <calcPr calcId="191029" fullCalcOnLoad="1"/>
</workbook>'''
    workbook_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>'''
    root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''
    core_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>
</cp:coreProperties>'''
    app_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
</Properties>'''

    image_entries: list[tuple[int, bytes, str]] = []
    for row_index, item in enumerate(results.get("items", []), start=2):
        fetched = _fetch_image_bytes(item.get("image_url", ""))
        if fetched:
            content, extension = fetched
            image_entries.append((row_index, content, extension))

    content_type_defaults = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
    ]
    if any(extension == "png" for _, _, extension in image_entries):
        content_type_defaults.append('<Default Extension="png" ContentType="image/png"/>')
    if any(extension == "jpeg" for _, _, extension in image_entries):
        content_type_defaults.append('<Default Extension="jpeg" ContentType="image/jpeg"/>')
    if any(extension == "gif" for _, _, extension in image_entries):
        content_type_defaults.append('<Default Extension="gif" ContentType="image/gif"/>')

    content_type_overrides = [
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    if image_entries:
        content_type_overrides.append('<Override PartName="/xl/drawings/drawing1.xml" ContentType="application/vnd.openxmlformats-officedocument.drawing+xml"/>')

    content_types = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  {''.join(content_type_defaults)}
  {''.join(content_type_overrides)}
</Types>'''

    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as zip_file:
        zip_file.writestr("[Content_Types].xml", content_types)
        zip_file.writestr("_rels/.rels", root_rels)
        zip_file.writestr("docProps/core.xml", core_xml)
        zip_file.writestr("docProps/app.xml", app_xml)
        zip_file.writestr("xl/workbook.xml", workbook_xml)
        zip_file.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zip_file.writestr("xl/worksheets/sheet1.xml", _worksheet_xml(results, bool(image_entries)))
        if image_entries:
            drawing_anchors = []
            drawing_relationships = []
            for image_index, (row_index, content, extension) in enumerate(image_entries, start=1):
                drawing_anchors.append(_drawing_anchor_xml(image_index, row_index - 1))
                drawing_relationships.append(
                    f'<Relationship Id="rId{image_index}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image{image_index}.{extension}"/>'
                )
                zip_file.writestr(f"xl/media/image{image_index}.{extension}", content)

            drawing_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<xdr:wsDr xmlns:xdr="http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  {''.join(drawing_anchors)}
</xdr:wsDr>'''
            drawing_rels_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  {''.join(drawing_relationships)}
</Relationships>'''
            sheet_rels_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/>
</Relationships>'''
            zip_file.writestr("xl/drawings/drawing1.xml", drawing_xml)
            zip_file.writestr("xl/drawings/_rels/drawing1.xml.rels", drawing_rels_xml)
            zip_file.writestr("xl/worksheets/_rels/sheet1.xml.rels", sheet_rels_xml)
    return buffer.getvalue()
