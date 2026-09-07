package samtoolsdk

import (
	"reflect"
	"strings"
)

// JSONSchema is a simplified JSON Schema representation for tool parameters.
// Exported so that DynamicSchemaFunc implementations can build and return
// alternate parameter schemas via SchemaOverride.Parameters.
type JSONSchema struct {
	Type       string         `json:"type"`
	Properties map[string]any `json:"properties,omitempty"`
	Required   []string       `json:"required,omitempty"`
}

// BuildSchema returns the JSON schema that the SDK would auto-generate for
// the parameter struct type T. It is intended for use from DynamicSchemaFunc
// implementations that swap the parameter shape based on per-agent tool_config
// (for example a data-access tool that exposes different fields for MongoDB
// vs DynamoDB backends).
//
// If T is not a struct type the returned schema has Type set to "object" and
// no properties. Artifact-typed fields are rendered in the schema exactly as
// they are by NewTool.
func BuildSchema[T any]() *JSONSchema {
	var zero T
	t := reflect.TypeOf(zero)
	if t == nil {
		return &JSONSchema{Type: "object"}
	}
	for t.Kind() == reflect.Ptr {
		t = t.Elem()
	}
	schema, _ := schemaFromStruct(t)
	return schema
}

// artifactParamInfo describes an artifact-typed parameter.
//
// FilenameKey is set when the param is a list of structured objects where the
// artifact filename lives at a named JSON field on each element (e.g. Python's
// concatenate_audio clips_to_join: [{filename, pause_after_ms}]). When unset,
// the param is a flat Artifact / *Artifact / []Artifact as before.
type artifactParamInfo struct {
	IsList      bool   `json:"is_list"`
	IsOptional  bool   `json:"is_optional"`
	FilenameKey string `json:"filename_key,omitempty"`
}

// schemaFromStruct generates a JSON Schema and artifact parameter info from a Go struct type.
//
// Rules:
//   - Non-pointer fields are required; pointer fields are optional.
//   - json:"name" tag provides the JSON property name.
//   - desc:"..." tag provides the LLM-visible description.
//   - Artifact / *Artifact / []Artifact fields are detected as artifact params
//     and presented as string / string / array-of-strings to the LLM.
//   - []T where T is a struct with exactly one string field tagged
//     `artifact:"filename"` becomes a structured artifact-list param: the
//     schema is array-of-object (Python-compatible) and the SDK treats each
//     element's filename field as the artifact reference.
//   - Go types map: string→"string", int*→"integer", float*→"number",
//     bool→"boolean", []T→"array", map→"object", struct→"object" (recursive).
func schemaFromStruct(t reflect.Type) (*JSONSchema, map[string]artifactParamInfo) {
	// Unwrap pointer types.
	for t.Kind() == reflect.Ptr {
		t = t.Elem()
	}

	if t.Kind() != reflect.Struct {
		return &JSONSchema{Type: "object"}, nil
	}

	props := make(map[string]any)
	var required []string
	artifactParams := make(map[string]artifactParamInfo)

	for i := range t.NumField() {
		field := t.Field(i)

		// Skip unexported fields.
		if !field.IsExported() {
			continue
		}

		// Get JSON name.
		name := jsonFieldName(field)
		if name == "-" {
			continue
		}

		// Get description from desc tag.
		desc := field.Tag.Get("desc")

		fieldType := field.Type
		isPointer := fieldType.Kind() == reflect.Ptr

		// Unwrap pointer for type analysis.
		elemType := fieldType
		if isPointer {
			elemType = fieldType.Elem()
		}

		// Check for artifact types.
		if isArtifactType(elemType) {
			// Single artifact (required or optional).
			prop := map[string]any{
				"type": "string",
			}
			if desc != "" {
				prop["description"] = desc
			}
			props[name] = prop
			artifactParams[name] = artifactParamInfo{
				IsList:     false,
				IsOptional: isPointer,
			}
			if !isPointer {
				required = append(required, name)
			}
			continue
		}

		if elemType.Kind() == reflect.Slice && isArtifactType(elemType.Elem()) {
			// []Artifact — list of artifacts.
			prop := map[string]any{
				"type":  "array",
				"items": map[string]any{"type": "string"},
			}
			if desc != "" {
				prop["description"] = desc
			}
			props[name] = prop
			artifactParams[name] = artifactParamInfo{
				IsList:     true,
				IsOptional: isPointer,
			}
			if !isPointer {
				required = append(required, name)
			}
			continue
		}

		// []StructWithFilenameTag — structured artifact-list (Python-compatible).
		if elemType.Kind() == reflect.Slice && elemType.Elem().Kind() == reflect.Struct {
			if key, ok := filenameTagField(elemType.Elem()); ok {
				nested, _ := schemaFromStruct(elemType.Elem())
				items := map[string]any{"type": "object"}
				if len(nested.Properties) > 0 {
					items["properties"] = nested.Properties
				}
				if len(nested.Required) > 0 {
					items["required"] = nested.Required
				}
				prop := map[string]any{
					"type":  "array",
					"items": items,
				}
				if desc != "" {
					prop["description"] = desc
				}
				props[name] = prop
				artifactParams[name] = artifactParamInfo{
					IsList:      true,
					IsOptional:  isPointer,
					FilenameKey: key,
				}
				if !isPointer {
					required = append(required, name)
				}
				continue
			}
		}

		// Regular field — map Go type to JSON Schema.
		prop := goTypeToSchema(elemType)
		if desc != "" {
			prop["description"] = desc
		}

		props[name] = prop

		if !isPointer {
			required = append(required, name)
		}
	}

	schema := &JSONSchema{
		Type:       "object",
		Properties: props,
		Required:   required,
	}

	return schema, artifactParams
}

// goTypeToSchema maps a Go reflect.Type to a JSON Schema property map.
func goTypeToSchema(t reflect.Type) map[string]any {
	switch t.Kind() {
	case reflect.String:
		return map[string]any{"type": "string"}

	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64,
		reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
		return map[string]any{"type": "integer"}

	case reflect.Float32, reflect.Float64:
		return map[string]any{"type": "number"}

	case reflect.Bool:
		return map[string]any{"type": "boolean"}

	case reflect.Slice:
		items := goTypeToSchema(t.Elem())
		return map[string]any{
			"type":  "array",
			"items": items,
		}

	case reflect.Map:
		return map[string]any{"type": "object"}

	case reflect.Struct:
		// Recursive: generate nested object schema.
		nested, _ := schemaFromStruct(t)
		result := map[string]any{"type": "object"}
		if len(nested.Properties) > 0 {
			result["properties"] = nested.Properties
		}
		if len(nested.Required) > 0 {
			result["required"] = nested.Required
		}
		return result

	case reflect.Ptr:
		return goTypeToSchema(t.Elem())

	default:
		return map[string]any{"type": "string"}
	}
}

// isArtifactType checks if a type is the Artifact struct.
func isArtifactType(t reflect.Type) bool {
	return t == reflect.TypeOf(Artifact{})
}

// filenameTagField returns the JSON name of the string field tagged
// `artifact:"filename"` on struct type t, if exactly one such field exists.
// It is used to detect structured artifact-list parameters like
// clips_to_join: [{filename, pause_after_ms}].
func filenameTagField(t reflect.Type) (string, bool) {
	if t.Kind() != reflect.Struct {
		return "", false
	}
	var match string
	found := 0
	for i := range t.NumField() {
		f := t.Field(i)
		if !f.IsExported() {
			continue
		}
		if f.Type.Kind() != reflect.String {
			continue
		}
		if f.Tag.Get("artifact") != "filename" {
			continue
		}
		match = jsonFieldName(f)
		found++
	}
	if found == 1 {
		return match, true
	}
	return "", false
}

// jsonFieldName extracts the JSON field name from a struct field.
// Returns the field name if no json tag is present.
func jsonFieldName(f reflect.StructField) string {
	tag := f.Tag.Get("json")
	if tag == "" {
		return f.Name
	}
	name, _, _ := strings.Cut(tag, ",")
	if name == "" {
		return f.Name
	}
	return name
}
