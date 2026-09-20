import xml.etree.ElementTree as etree
from pathlib import Path
from zipfile import ZipFile

WORKBOOK = Path(__file__).parents[1] / "tableau" / "manufacturing_intelligence_advanced_analytics.twbx"


def _tree() -> etree.ElementTree:
    with ZipFile(WORKBOOK) as archive:
        twb = next(name for name in archive.namelist() if name.endswith(".twb"))
        return etree.ElementTree(etree.fromstring(archive.read(twb)))


def test_package_is_sanitized_and_extract_only() -> None:
    with ZipFile(WORKBOOK) as archive:
        assert archive.testzip() is None
        names = archive.namelist()
        assert sum(name.endswith(".hyper") for name in names) == 2
        content = b"\n".join(archive.read(name) for name in names if name.endswith(".twb")).lower()
    for marker in (b"dbc-", b"databricks", b"v-http-path", b"warehouse", b"username=", b"password=", b"token="):
        assert marker not in content


def test_parameters_lods_calculations_and_actions_exist() -> None:
    tree = _tree()
    parameters = tree.find("./datasources/datasource[@name='Parameters']")
    assert parameters is not None
    assert len(parameters.findall("column")) == 2
    formulas = "\n".join(node.get("formula", "") for node in tree.iter("calculation"))
    for token in ("{ FIXED", "{ INCLUDE", "{ EXCLUDE"):
        assert token in formulas
    captions = {node.get("caption") for node in tree.iter("column")}
    assert {"Selected Metric", "Variance vs Benchmark", "Yield Loss Contribution", "Defect Contribution %", "Metric Status"} <= captions
    actions = tree.find("actions")
    assert actions is not None
    commands = [node.get("command") for node in actions.iter("command")]
    assert commands.count("tsc:tsl-filter") >= 2
    assert commands.count("tsc:brush") >= 1
    assert not actions.findall("nav-action")


def test_calculated_columns_precede_column_instances() -> None:
    tree = _tree()
    for datasource in tree.findall("./datasources/datasource"):
        children = list(datasource)
        instance_indexes = [
            index for index, child in enumerate(children) if child.tag == "column-instance"
        ]
        if not instance_indexes:
            continue
        first_instance = min(instance_indexes)
        calculation_indexes = [
            index
            for index, child in enumerate(children)
            if child.tag == "column" and child.get("name", "").startswith("[Calculation_PR13_")
        ]
        assert calculation_indexes
        assert max(calculation_indexes) < first_instance


def test_parameter_driven_calculations_are_wired_to_worksheets() -> None:
    tree = _tree()
    metric_instance = "[usr:Calculation_PR13_Selected_Metric:qk]"
    benchmark_instance = "[usr:Calculation_PR13_Selected_Benchmark:qk]"
    analysis_instance = "[usr:Calculation_PR13_Analysis_Value:qk]"
    active_instances = {
        "Selected Metric Trend": metric_instance,
        "Metric vs Benchmark Trend": analysis_instance,
        "Quality - Factory Comparison": analysis_instance,
        "Quality - Product Comparison": analysis_instance,
        "Quality - Line Comparison": analysis_instance,
    }
    for name, active_instance in active_instances.items():
        worksheet = tree.find(f"./worksheets/worksheet[@name='{name}']")
        assert worksheet is not None
        xml = etree.tostring(worksheet, encoding="unicode")
        assert metric_instance in xml
        table = worksheet.find("table")
        assert table is not None
        active_view_xml = "".join(
            etree.tostring(node, encoding="unicode")
            for node in (table.find("rows"), table.find("cols"), table.find("panes"))
            if node is not None
        )
        assert active_instance in active_view_xml
        assert "[usr:Calculation_0659753060524032:qk]" not in active_view_xml
        parameter_dependency = worksheet.find(
            ".//datasource-dependencies[@datasource='Parameters']"
        )
        assert parameter_dependency is not None
    for name in (
        "Quality - Factory Comparison",
        "Quality - Product Comparison",
        "Quality - Line Comparison",
    ):
        worksheet = tree.find(f"./worksheets/worksheet[@name='{name}']")
        assert worksheet is not None
        assert benchmark_instance in etree.tostring(worksheet, encoding="unicode")


def test_every_dashboard_worksheet_has_a_visual_representation() -> None:
    tree = _tree()
    worksheet_names = {
        node.get("name") for node in tree.findall("./worksheets/worksheet")
    }
    worksheet_windows = {
        node.get("name")
        for node in tree.findall("./windows/window[@class='worksheet']")
    }
    for dashboard in tree.findall("./dashboards/dashboard"):
        dashboard_name = dashboard.get("name")
        dashboard_window = tree.find(
            f"./windows/window[@class='dashboard'][@name='{dashboard_name}']"
        )
        assert dashboard_window is not None
        viewpoints = {
            node.get("name")
            for node in dashboard_window.findall("./viewpoints/viewpoint")
        }
        for zone in dashboard.findall(".//zone[@name]"):
            sheet_name = zone.get("name")
            if sheet_name not in worksheet_names:
                continue
            assert sheet_name in worksheet_windows
            assert sheet_name in viewpoints


def test_quality_comparisons_do_not_overlap() -> None:
    tree = _tree()
    dashboard = tree.find("./dashboards/dashboard[@name='Manufacturing Quality']")
    assert dashboard is not None
    expected = {
        "Quality - Factory Comparison": (667, 32888),
        "Quality - Product Comparison": (33555, 32889),
        "Quality - Line Comparison": (66444, 32889),
    }
    for name, (x, width) in expected.items():
        zone = dashboard.find(f"./zones/zone/zone[@name='{name}']")
        if zone is None:
            zone = dashboard.find(f".//zone[@name='{name}']")
        assert zone is not None
        assert int(zone.get("x")) == x
        assert int(zone.get("w")) == width
    for zone_id in ("20", "21", "22"):
        wrapper = dashboard.find(f".//zone[@id='{zone_id}']")
        assert wrapper is not None
        assert wrapper.get("w") == "32888"
        assert wrapper.get("h") == "23500"


def test_dashboard_controls_and_scroll_sensitive_charts_have_enough_height() -> None:
    tree = _tree()
    expected_parameter_heights = {
        "Executive Overview": 6500,
        "Manufacturing Quality": 5750,
    }
    for dashboard_name, expected_height in expected_parameter_heights.items():
        dashboard = tree.find(f"./dashboards/dashboard[@name='{dashboard_name}']")
        assert dashboard is not None
        controls = dashboard.findall("./zones/zone[@type-v2='paramctrl']")
        assert len(controls) == 2
        assert all(int(control.get("h")) == expected_height for control in controls)
        for control in controls:
            formats = {
                node.get("attr"): node.get("value")
                for node in control.findall("./zone-style/format")
            }
            assert formats.get("border-style") == "none"
            assert formats.get("border-width") == "0"
            assert "background-color" not in formats

    quality = tree.find("./dashboards/dashboard[@name='Manufacturing Quality']")
    assert quality is not None
    line = quality.find(".//zone[@name='Quality - Line Comparison']")
    assert line is not None and line.get("h") == "23500"

    rca = tree.find("./dashboards/dashboard[@name='Root Cause Analysis']")
    assert rca is not None
    supplier = rca.find(".//zone[@name='RCA - Supplier Contribution']")
    assert supplier is not None and supplier.get("h") == "34436"


def test_right_side_color_controls_follow_filters_and_parameters() -> None:
    tree = _tree()
    for dashboard in tree.findall("./dashboards/dashboard"):
        # Check the default dashboard zones; device-layout copies reuse the
        # same ids and are updated by the generator at the same time.
        zones = dashboard.find("./zones")
        assert zones is not None
        controls = list(zones.iter("zone"))
        colors = [node for node in controls if node.get("type-v2") == "color"]
        if not colors:
            continue
        preceding = [
            node
            for node in controls
            if node.get("type-v2") in {"filter", "paramctrl"}
        ]
        assert preceding
        last_preceding_bottom = max(
            int(node.get("y")) + int(node.get("h")) for node in preceding
        )
        first_color_y = min(int(node.get("y")) for node in colors)
        assert first_color_y >= last_preceding_bottom
        top_level_colors = dashboard.findall("./zones/zone[@type-v2='color']")
        assert len(top_level_colors) == len(colors)


def test_color_controls_are_positioned_beside_their_charts() -> None:
    tree = _tree()
    quality = tree.find("./dashboards/dashboard[@name='Manufacturing Quality']")
    assert quality is not None
    expected_quality = {
        "18": (36667, 34000),
        "34": (36667, 81833),
    }
    for zone_id, (x, y) in expected_quality.items():
        color = quality.find(f"./zones/zone[@id='{zone_id}']")
        assert color is not None and color.get("type-v2") == "color"
        assert (int(color.get("x")), int(color.get("y"))) == (x, y)

    rework_colors = [
        node
        for node in quality.findall("./zones/zone[@type-v2='color']")
        if node.get("name") == "Quality - Rework and Scrap Trend"
    ]
    assert len(rework_colors) == 1
    rework_color = rework_colors[0]
    assert (int(rework_color.get("x")), int(rework_color.get("y"))) == (
        86000,
        34000,
    )

    volume = quality.find(".//zone[@name='Quality - Volume and Fail Trend']")
    rework = quality.find(".//zone[@name='Quality - Rework and Scrap Trend']")
    assert volume is not None and rework is not None
    assert volume.get("w") == rework.get("w") == "36000"

    rca = tree.find("./dashboards/dashboard[@name='Root Cause Analysis']")
    assert rca is not None
    defect_color = rca.find("./zones/zone[@id='15']")
    assert defect_color is not None and defect_color.get("type-v2") == "color"
    assert (int(defect_color.get("x")), int(defect_color.get("y"))) == (
        86000,
        71464,
    )


def test_line_comparison_uses_renderable_selected_metric_view() -> None:
    tree = _tree()
    worksheet = tree.find(
        "./worksheets/worksheet[@name='Quality - Line Comparison']"
    )
    assert worksheet is not None
    assert "[none:line_id:nk]" in (worksheet.findtext("./table/rows") or "")
    assert "[usr:Calculation_PR13_Analysis_Value:qk]" in (
        worksheet.findtext("./table/cols") or ""
    )
    active_view = "".join(
        etree.tostring(node, encoding="unicode")
        for node in (
            worksheet.find("./table/rows"),
            worksheet.find("./table/cols"),
            worksheet.find("./table/panes"),
        )
        if node is not None
    )
    assert "Calculation_PR13_Exclude_Line" not in active_view
    tooltip = worksheet.find(
        "./table/panes/pane/customized-tooltip/formatted-text"
    )
    assert tooltip is not None
    assert (tooltip.find("run").text or "").startswith("Line Id")


def test_rca_contributor_axes_remain_renderable() -> None:
    tree = _tree()
    defect_quantity = "[sum:defect_quantity:qk]"
    component = tree.find(
        "./worksheets/worksheet[@name='RCA - Component Contribution']"
    )
    supplier = tree.find(
        "./worksheets/worksheet[@name='RCA - Supplier Contribution']"
    )
    assert component is not None and supplier is not None
    assert defect_quantity in (component.findtext("./table/cols") or "")
    assert defect_quantity in (supplier.findtext("./table/cols") or "")
    for worksheet in (component, supplier):
        worksheet_xml = etree.tostring(worksheet, encoding="unicode")
        assert "Calculation_PR13" not in worksheet_xml


def test_rca_scope_filters_apply_to_every_view() -> None:
    tree = _tree()
    defect_source = next(
        datasource.get("name")
        for datasource in tree.findall("./datasources/datasource")
        if datasource.get("caption", "").startswith("gold_defect_pareto")
    )
    expected = {
        "factory_id": "8",
        "product_id": "9",
        "line_id": "10",
        "component_id": "11",
        "supplier_id": "12",
        "defect_name": "13",
    }
    for sheet_name in (
        "RCA - Defect Trend",
        "RCA - Defect Pareto",
        "RCA - Component Contribution",
        "RCA - Supplier Contribution",
    ):
        worksheet = tree.find(f"./worksheets/worksheet[@name='{sheet_name}']")
        assert worksheet is not None
        for field, group in expected.items():
            ref = f"[{defect_source}].[none:{field}:nk]"
            node = worksheet.find(f"./table/view/filter[@column='{ref}']")
            assert node is not None
            assert node.get("filter-group") == group

    dashboard = tree.find("./dashboards/dashboard[@name='Root Cause Analysis']")
    assert dashboard is not None
    filter_params = {
        node.get("param")
        for node in dashboard.findall(".//zone[@type-v2='filter']")
    }
    for field in expected:
        assert f"[{defect_source}].[none:{field}:nk]" in filter_params


def test_every_dashboard_filter_applies_to_every_dashboard_worksheet() -> None:
    tree = _tree()
    worksheet_names = {
        node.get("name") for node in tree.findall("./worksheets/worksheet")
    }
    for dashboard in tree.findall("./dashboards/dashboard"):
        dashboard_sheets = {
            zone.get("name")
            for zone in dashboard.findall(".//zone[@name]")
            if zone.get("name") in worksheet_names
        }
        controls = {
            (zone.get("name"), zone.get("param"))
            for zone in dashboard.findall(".//zone[@type-v2='filter']")
        }
        for owner_name, field_ref in controls:
            owner = tree.find(
                f"./worksheets/worksheet[@name='{owner_name}']"
            )
            assert owner is not None
            owner_filter = owner.find(
                f"./table/view/filter[@column='{field_ref}']"
            )
            assert owner_filter is not None
            filter_group = owner_filter.get("filter-group")
            assert filter_group is not None
            for sheet_name in dashboard_sheets:
                worksheet = tree.find(
                    f"./worksheets/worksheet[@name='{sheet_name}']"
                )
                assert worksheet is not None
                target_filter = worksheet.find(
                    f"./table/view/filter[@filter-group='{filter_group}']"
                )
                assert target_filter is not None
                assert target_filter.get("column") == field_ref


def test_marks_encodings_use_tableau_supported_elements() -> None:
    tree = _tree()
    allowed = {
        "color",
        "size",
        "text",
        "shape",
        "wedge-size",
        "lod",
        "geometry",
        "image",
        "tooltip",
        "path",
        "level",
        "edge",
        "custom",
    }
    for encodings in tree.findall(".//encodings"):
        assert {node.tag for node in encodings} <= allowed


def test_parameter_driven_kpi_cards_are_visible() -> None:
    tree = _tree()
    expectations = {
        "KPI - FPY": (
            "[usr:Calculation_PR13_Selected_Metric:qk]",
            "Selected Metric",
        ),
        "KPI - WoW FPY Change": (
            "[usr:Calculation_PR13_Variance_Display:nk]",
            "Variance vs Benchmark",
        ),
    }
    for name, (instance, label) in expectations.items():
        worksheet = tree.find(f"./worksheets/worksheet[@name='{name}']")
        assert worksheet is not None
        xml = etree.tostring(worksheet, encoding="unicode")
        assert instance in xml
        assert label in xml
        assert worksheet.find(
            ".//datasource-dependencies[@datasource='Parameters']"
        ) is not None


def test_all_metrics_have_selectable_benchmarks_and_nonblank_variance() -> None:
    tree = _tree()
    datasource = next(
        node
        for node in tree.findall("./datasources/datasource")
        if node.get("caption", "").startswith("gold_manufacturing_daily")
    )
    for metric in ("FPY", "Defect_Rate", "DPPM", "Rework_Rate", "Scrap_Rate"):
        for level in ("Overall", "Factory", "Product"):
            field = datasource.find(
                f"column[@name='[Calculation_PR13_{level}_{metric}]']"
            )
            assert field is not None
            formula = field.find("calculation").get("formula")
            assert "{ FIXED" in formula

    selected = datasource.find(
        "column[@name='[Calculation_PR13_Selected_Benchmark]']/calculation"
    )
    assert selected is not None
    selected_formula = selected.get("formula")
    for member in ("FPY", "Defect Rate", "DPPM", "Rework Rate", "Scrap Rate"):
        assert f"WHEN '{member}'" in selected_formula
    for level in ("Overall", "Factory", "Product"):
        assert f"WHEN '{level}'" in selected_formula

    variance = datasource.find(
        "column[@name='[Calculation_PR13_Variance]']/calculation"
    )
    assert variance is not None
    assert variance.get("formula") == (
        "[Calculation_PR13_Selected_Metric] - "
        "[Calculation_PR13_Selected_Benchmark]"
    )
    display = datasource.find(
        "column[@name='[Calculation_PR13_Variance_Display]']/calculation"
    )
    assert display is not None
    assert "DPPM" in display.get("formula")
    assert " pp" in display.get("formula")
