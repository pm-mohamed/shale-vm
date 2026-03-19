// NOTE: This file is a reference copy obtained from the virtual machine.
// It is NOT used directly in the codebase — we maintain it here so that
// changes can be developed and reviewed in version control, then manually
// deployed to the VM. The actual production script is script.jsx.

//@include "libs/json2.js"

var MM_TO_PT = 2.834645669;
var WIDEN_MM = 3;              // how much to try expanding rightward (adjustable)
var WIDEN_PT = WIDEN_MM * MM_TO_PT;
var MIN_FRAME_WIDTH_MM = 20;   // skip frames narrower than this (icons, badges)
var MIN_FRAME_WIDTH_PT = MIN_FRAME_WIDTH_MM * MM_TO_PT;
var COL_GAP_MM = 5;            // reserved gap between left and right columns
var COL_GAP_PT = COL_GAP_MM * MM_TO_PT;
var EDGE_MARGIN_MM = 3;        // margin from artboard right edge
var EDGE_MARGIN_PT = EDGE_MARGIN_MM * MM_TO_PT;
var LARGE_LABEL_MIN_PT = 7.1;  // minimum font size for labels >= 80 cm²
var SMALL_LABEL_MIN_PT = 5.0;  // minimum font size for labels < 80 cm²
var LARGE_LABEL_THRESHOLD_CM2 = 80;

// Frames that use tab stops for column alignment — must keep original
// template width so headers and data rows stay vertically aligned.
var TABBED_FRAMES = {
    "IngredientsTableColumnNames": true, "IngredientsTableCells": true,
    "TableColumnNames": true, "TableCells": true
};

var UNIFIED_TRACKING_LAYERS = ["Logo", "Layout", "Languages"];
var UNIFIED_TRACKING = 0;

// Returns true if a text frame relies on tab stops for alignment.
function hasTabStops(tf) {
    try {
        var tabs = tf.textRange.paragraphAttributes.tabStops;
        return (tabs && tabs.length > 0);
    } catch (e) { return false; }
}

// Parses a label size string like "325x138mm" or "BN-100x45mm" into
// surface area in cm². Ignores any prefix before the dimensions.
// Returns null if no dimensions are found.
function parseLabelAreaCm2(labelSize) {
    var match = labelSize.match(/(\d+)x(\d+)mm$/i);
    if (!match) return null;
    var widthMm = parseInt(match[1], 10);
    var heightMm = parseInt(match[2], 10);
    return (widthMm * heightMm) / 100; // mm² to cm²
}

// Returns the legal minimum font size in points based on label surface area.
// Defaults to the stricter 7.1pt if parsing fails (fail-safe).
function getMinFontSize(labelSize) {
    var areaCm2 = parseLabelAreaCm2(labelSize);
    if (areaCm2 === null) return LARGE_LABEL_MIN_PT;
    return (areaCm2 >= LARGE_LABEL_THRESHOLD_CM2) ? LARGE_LABEL_MIN_PT : SMALL_LABEL_MIN_PT;
}

// Iterates every character in every text frame in the given config layers
// and bumps any font size below the legal minimum. Only touches layers
// the script already works with to avoid crashing on artwork/design layers
// that may contain locked groups.
function enforceMinFontSize(doc, minPt, configLayers) {
    for (var i = 0; i < configLayers.length; i++) {
        try {
            var layer = doc.layers.getByName(configLayers[i].name);
            for (var f = 0; f < layer.textFrames.length; f++) {
                try {
                    var tf = layer.textFrames[f];
                    if (tf.locked || tf.hidden) continue;
                    var chars = tf.textRange.characters;
                    for (var c = 0; c < chars.length; c++) {
                        if (chars[c].characterAttributes.size < minPt) {
                            chars[c].characterAttributes.size = minPt;
                        }
                    }
                } catch (e) {
                    // Skip frames that error
                }
            }
        } catch (e) {
            // Layer not found — skip
        }
    }
}

// Resets tracking (letter spacing) to a uniform value on all text frames
// across Logo, Layout, and Languages layers so no template-level
// inconsistencies carry into the output.
function unifyTracking(doc) {
    for (var i = 0; i < UNIFIED_TRACKING_LAYERS.length; i++) {
        try {
            var layer = doc.layers.getByName(UNIFIED_TRACKING_LAYERS[i]);
            for (var f = 0; f < layer.textFrames.length; f++) {
                try {
                    var tf = layer.textFrames[f];
                    if (tf.locked || tf.hidden) continue;
                    var chars = tf.textRange.characters;
                    for (var c = 0; c < chars.length; c++) {
                        chars[c].characterAttributes.tracking = UNIFIED_TRACKING;
                    }
                } catch (e) { /* skip frames that error */ }
            }
        } catch (e) { /* layer not found — skip */ }
    }
}

function loadConfigFromJsonFile(filePath) {
    var file = new File(filePath);
    if (!file.exists) {
        return null;
    }

    file.open("r");
    var content = file.read();
    file.close();

    return JSON.parse(content);
}

// Helper function to detect bold and regular font variants from a text frame
function detectFrameFonts(textFrame) {
    var result = { boldFont: "ArticulatCF-DemiBold", regularFont: "ArticulatCF-Regular" };

    if (!textFrame || textFrame.textRange.characters.length === 0) {
        return result;
    }

    var boldPatterns = ["Bold", "DemiBold", "Semibold", "SemiBold", "Heavy", "Black"];
    var seenFonts = {};
    var foundBold = null;
    var foundMedium = null;
    var foundRegular = null;

    for (var i = 0; i < textFrame.textRange.characters.length; i++) {
        var fontName = textFrame.textRange.characters[i].characterAttributes.textFont.name;
        if (seenFonts[fontName]) continue;
        seenFonts[fontName] = true;

        var isBold = false;
        for (var b = 0; b < boldPatterns.length; b++) {
            if (fontName.indexOf(boldPatterns[b]) !== -1) {
                isBold = true;
                break;
            }
        }

        if (isBold) {
            if (!foundBold) foundBold = fontName;
        } else if (fontName.indexOf("Medium") !== -1) {
            if (!foundMedium) foundMedium = fontName;
        } else {
            if (!foundRegular) foundRegular = fontName;
        }
    }

    // Use detected fonts, promoting Medium to bold only if no primary bold found
    if (foundBold) result.boldFont = foundBold;
    else if (foundMedium) result.boldFont = foundMedium;

    if (foundRegular) result.regularFont = foundRegular;

    // If only one weight was found, use it for both roles
    if (!foundBold && !foundMedium && foundRegular) result.boldFont = foundRegular;
    if (!foundRegular && foundBold) result.regularFont = foundBold;
    if (!foundRegular && !foundBold && foundMedium) result.regularFont = foundMedium;

    return result;
}

// Helper function to replace text
function replaceTextInFrame(textFrame, newText, prefix) {
    if (!textFrame) return;

    var paragraphAttributes = textFrame.textRange.paragraphAttributes;
    var tabs = paragraphAttributes.tabStops; // Save existing tab stops

    // Ensure tab stops have no leader
    for (var i = 0; i < tabs.length; i++) {
        tabs[i].leader = ""; // Clear any existing leader
    }

    // Detect font variants from the existing template text
    var fonts = detectFrameFonts(textFrame);
    var prefixFont = fonts.boldFont;
    var textFont = fonts.regularFont;

    // Replace the text content while preserving the style
    var styledText = textFrame.textRange;

    if (prefix) {
        styledText.contents = prefix + newText;

        for (var i = 0; i < styledText.characters.length; i++) {
            var character = styledText.characters[i];
            if (i < prefix.length) {
                // Apply demi bold style to the prefix
                character.characterAttributes.textFont = app.textFonts.getByName(prefixFont);
            } else {
                // Apply regular style to the newText
                character.characterAttributes.textFont = app.textFonts.getByName(textFont);
            }
        }
    } else {
        styledText.contents = newText;
        for (var i = 0; i < styledText.characters.length; i++) {
            styledText.characters[i].characterAttributes.textFont = app.textFonts.getByName(textFont);
        }
    }

    // Reapply the custom tabs
    styledText.paragraphAttributes.tabStops = tabs;
}

// Helper function to replace text and apply superscript formatting to '*'
function formatAsterisks(textFrame) {
    if (!textFrame) return;

    var styledText = textFrame.textRange;

    // Apply superscript formatting to '*'
    for (var i = 0; i < styledText.characters.length; i++) {
        var character = styledText.characters[i];
        if (character.contents === '*') {
            character.characterAttributes.baselinePosition = FontBaselineOption.SUPERSCRIPT;
        }
    }
}

// Recursive function to process layers, groups, and text frames
function processElement(parentElement, configElement) {
    if (!configElement) return;

    // Process text frames
    if (configElement.textFrames) {
        for (var i = 0; i < configElement.textFrames.length; i++) {
            var configTextFrame = configElement.textFrames[i];
            var textFrame;
            try {
                textFrame = parentElement.textFrames.getByName(configTextFrame.name);
                replaceTextInFrame(textFrame, configTextFrame.content, configTextFrame.prefix);
                if (configTextFrame.name === "TableColumnNames") {
                    formatAsterisks(textFrame);
                }
            } catch (e) {
                if (configTextFrame.optional) {
                    continue;
                }
                throw new Error("Error: Text frame '" + configTextFrame.name + "' not found in parent element '" + parentElement.name + "'.");
            }
        }
    }

    // Process groups recursively
    if (configElement.groups) {
        for (var j = 0; j < configElement.groups.length; j++) {
            var configGroup = configElement.groups[j];
            var group;
            try {
                group = parentElement.groupItems.getByName(configGroup.name);
                processElement(group, configGroup);
            } catch (e) {
                throw new Error("Error: Group '" + configGroup.name + "' not found in parent element '" + parentElement.name + "'.");
            }
        }
    }
}

function insertBarcode(doc, barcodeFile) {
    const PLACEHOLDER_NAME = "BarcodePlaceholder";
    const PLACEHOLDER_LAYER = "Barcode+Recycling";
    const PLACEHOLDER_GROUP = "BarcodeGroup";

    var layer, group, placeholder;

    try {
        layer = doc.layers.getByName(PLACEHOLDER_LAYER);
    } catch (e) {
        throw new Error("Error: Layer '" + PLACEHOLDER_LAYER + "' not found.");
    }

    try {
        group = layer.groupItems.getByName(PLACEHOLDER_GROUP);
    } catch (e) {
        throw new Error("Error: Group '" + PLACEHOLDER_GROUP + "' not found in layer '" + PLACEHOLDER_LAYER + "'.");
    }

    try {
        placeholder = group.pageItems.getByName(PLACEHOLDER_NAME);
    } catch (e) {
        throw new Error("Error: Placeholder '" + PLACEHOLDER_NAME + "' not found in group '" + PLACEHOLDER_GROUP + "'.");
    }

    var position = [placeholder.left, placeholder.top];
    var size = [placeholder.width, placeholder.height];

    placeholder.remove();

    // Place the new barcode
    var placedItem = doc.placedItems.add();
    placedItem.file = barcodeFile;
    placedItem.name = "Barcode";

	// Set the barcode position and size
    // Get intrinsic dimensions of the placed barcode
    var originalWidth = placedItem.width;
    var originalHeight = placedItem.height;
    var originalRatio = originalWidth / originalHeight;
    var placeholderRatio = size[0] / size[1];

    if (originalRatio > placeholderRatio) {
        // Fit to placeholder width
        placedItem.width = size[0];
        placedItem.height = size[0] / originalRatio;
    } else {
        // Fit to placeholder height
        placedItem.height = size[1];
        placedItem.width = size[1] * originalRatio;
    }

    // Center the barcode within the placeholder area
    var newX = position[0] + (size[0] - placedItem.width) / 2;
    var newY = position[1] - (size[1] - placedItem.height) / 2;
    placedItem.position = [newX, newY];

    placedItem.move(group, ElementPlacement.PLACEATBEGINNING);

    placedItem.embed();
}

function getArtboardForFrame(doc, tf) {
    var cx = tf.left + tf.width / 2;
    var cy = tf.top - tf.height / 2;
    for (var i = 0; i < doc.artboards.length; i++) {
        var r = doc.artboards[i].artboardRect; // [left, top, right, bottom]
        if (cx >= r[0] && cx <= r[2] && cy <= r[1] && cy >= r[3]) {
            return r;
        }
    }
    return null;
}

function widenTextFrames(doc) {
    try {
        var layer = doc.layers.getByName("Languages");
        // layer.textFrames includes ALL descendant text frames — no recursion needed
        for (var i = 0; i < layer.textFrames.length; i++) {
            try {
                var tf = layer.textFrames[i];
                if (tf.kind !== TextType.AREATEXT) continue;
                if (tf.locked) continue;
                if (tf.width < MIN_FRAME_WIDTH_PT) continue;
                if (TABBED_FRAMES[tf.name] || hasTabStops(tf)) continue;

                var abRect = getArtboardForFrame(doc, tf);
                if (!abRect) continue;

                var abCenterX = (abRect[0] + abRect[2]) / 2;
                var leftColBoundary = abCenterX - COL_GAP_PT;

                // If the frame starts before the left-column boundary it is
                // a left-column frame; otherwise it belongs to the right column.
                // This guarantees maxRight > tf.left for every frame.
                var maxRight;
                if (tf.left < leftColBoundary) {
                    maxRight = leftColBoundary;
                } else {
                    maxRight = abRect[2] - EDGE_MARGIN_PT;
                }

                var currentRight = tf.left + tf.width;

                // Fix frames already overflowing their column
                if (currentRight > maxRight) {
                    tf.width = maxRight - tf.left;
                    continue;
                }

                // Widen frames that have room
                var newRight = Math.min(currentRight + WIDEN_PT, maxRight);
                if (newRight <= currentRight) continue;

                tf.width = newRight - tf.left;
            } catch (e) {
                // Skip frames that can't be modified
            }
        }
    } catch (e) {
        // Layer not found or error, skip widening entirely
    }
}

// Left-column groups (FR and ES sit on the left of their artboard)
var LEFT_GROUPS = {"FrGroup": true, "EsGroup": true};

// Post-placement safety net: clamp every text frame inside the known
// language groups so nothing extends past its column boundary.
// Uses group names to determine column side — bypasses all per-frame
// detection that widenTextFrames relies on (AREATEXT, locked, min-width,
// artboard-center heuristic).
function clampOverflowingFrames(doc) {
    try {
        var layer = doc.layers.getByName("Languages");

        for (var g = 0; g < layer.groupItems.length; g++) {
            try {
                var group = layer.groupItems[g];
                var isLeft = (LEFT_GROUPS[group.name] === true);

                // Locate the artboard that contains this group
                var abRect = null;
                for (var a = 0; a < doc.artboards.length; a++) {
                    var r = doc.artboards[a].artboardRect;
                    // Use the first text frame's position as a reliable anchor
                    if (group.textFrames.length > 0) {
                        var anchor = group.textFrames[0];
                        var ax = anchor.left + anchor.width / 2;
                        var ay = anchor.top - anchor.height / 2;
                        if (ax >= r[0] && ax <= r[2] && ay <= r[1] && ay >= r[3]) {
                            abRect = r;
                            break;
                        }
                    }
                }
                if (!abRect) continue;

                var abCenterX = (abRect[0] + abRect[2]) / 2;
                var maxRight = isLeft
                    ? (abCenterX - COL_GAP_PT)
                    : (abRect[2] - EDGE_MARGIN_PT);

                // Clamp every text frame in the group (skip tabbed table frames)
                for (var i = 0; i < group.textFrames.length; i++) {
                    try {
                        var tf = group.textFrames[i];
                        if (TABBED_FRAMES[tf.name] || hasTabStops(tf)) continue;
                        if (tf.left + tf.width > maxRight) {
                            tf.width = maxRight - tf.left;
                        }
                    } catch (e) { /* skip unmodifiable frames */ }
                }
            } catch (e) { /* skip groups that error */ }
        }
    } catch (e) { /* Languages layer missing — nothing to clamp */ }
}

function logError(message) {
    try {
        var scriptFolder = File($.fileName).parent;
        var logsFolder = new Folder(scriptFolder + "/logs");

        // Ensure the logs folder exists
        if (!logsFolder.exists) {
            logsFolder.create();
        }

        // Generate a unique log file name using date and time
        var now = new Date();
        var timestamp = now.getFullYear() + "-" +
                        ("0" + (now.getMonth() + 1)).slice(-2) + "-" +
                        ("0" + now.getDate()).slice(-2) + "_" +
                        ("0" + now.getHours()).slice(-2) + "-" +
                        ("0" + now.getMinutes()).slice(-2) + "-" +
                        ("0" + now.getSeconds()).slice(-2);

        var logFile = new File(logsFolder + "/log_" + timestamp + ".txt");

        // Open file for writing
        logFile.open("w");
        logFile.writeln("Error Log - " + now);
        logFile.writeln("---------------------------------");
        logFile.writeln(message);
        logFile.close();
    } catch (e) {
        throw new Error("Failed to write log: " + e.message);
    }
}


function main() {
    var doc = null;

	app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;

    try {
        var scriptFolder = File($.fileName).parent;
        var configPath = scriptFolder + "/temp/config.json";
        var config = loadConfigFromJsonFile(configPath);

        if (!config || !config.labelSize) {
            throw new Error("Configuration missing or invalid.");
        }

        var barcodePath = scriptFolder + "/temp/barcode.eps";
        var barcodeFile = new File(barcodePath);
        if (!barcodeFile.exists) {
            throw new Error("Barcode file not found.");
        }

        var illustratorFileName = config.labelSize + ".ai";
        var labelPath = scriptFolder + "/labels/" + illustratorFileName;
        var illustratorFile = new File(labelPath);

        if (!illustratorFile.exists) {
            throw new Error("Illustrator file not found.");
        }

        doc = app.open(illustratorFile);

        // Widen text frames to fill available label width
        widenTextFrames(doc);

        // Process each layer in the configuration
        if (config.layers) {
            for (var i = 0; i < config.layers.length; i++) {
                var configLayer = config.layers[i];
				var layer;
                try {
                    layer = doc.layers.getByName(configLayer.name);
                } catch (e) {
                    throw new Error("Error: Layer '" + configLayer.name + "' not found. " + e.message);
                }

				processElement(layer, configLayer);
            }
        }

        // Unify tracking on all label text blocks
        unifyTracking(doc);

        // Clamp any frames that still overflow their column boundary
        clampOverflowingFrames(doc);

        // Enforce legal minimum font size on translated language text.
        // Only the Languages layer is enforced — the Layout/Logo layers
        // use font sizes set by the template designer for each label size.
        var minFontSize = getMinFontSize(config.labelSize);
        var langLayers = [];
        for (var li = 0; li < config.layers.length; li++) {
            if (config.layers[li].name === "Languages") {
                langLayers.push(config.layers[li]);
            }
        }
        enforceMinFontSize(doc, minFontSize, langLayers);

        insertBarcode(doc, barcodeFile);

		var outputFolder = new Folder(scriptFolder + "/temp/output");
        if (!outputFolder.exists) {
            outputFolder.create();
        }

        var outputFilePath = scriptFolder + "/temp/output/output.ai";
        var outputFile = new File(outputFilePath);
        var saveOptions = new IllustratorSaveOptions();
        saveOptions.pdfCompatible = false;

		// wait a short while (0.5 seconds) to let previous operations settle
        $.sleep(500);

		// Retry mechanism for saving the file
        var saveSuccess = false;
        var attempts = 0;
        while (!saveSuccess && attempts < 3) {
            try {
                doc.saveAs(outputFile, saveOptions);
                saveSuccess = true;
            } catch (e) {
                attempts++;
                $.sleep(1000);
            }
        }
        if (!saveSuccess) {
            throw new Error("Failed to save file after several attempts.");
        }

		// wait a short while (0.5 seconds) to let previous operations settle
        $.sleep(500);
    } catch (e) {
		try {
			logError("Script error: " + e.message);
		} catch (e) {
		}
    } finally {
        if (doc) {
            doc.close(SaveOptions.DONOTSAVECHANGES);
        }
    }
}

// Run the main function
main();
