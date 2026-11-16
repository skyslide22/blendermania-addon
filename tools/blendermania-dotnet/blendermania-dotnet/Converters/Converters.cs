using System.Text.Json;
using System.Text.Json.Serialization;
using GBX.NET;
using static GBX.NET.Engines.Game.CGameCtnAnchoredObject;

namespace blendermania_dotnet;


public class EPhaseOffsetConverter : JsonConverter<EPhaseOffset?>
{
    public override EPhaseOffset? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? enumString = reader.GetString();
        if (enumString == null)
        {
            return null;
        }
        else if (Enum.TryParse(enumString, out EPhaseOffset enumValue))
        {
            return enumValue;
        }
        throw new JsonException($"Unable to parse '{enumString}' as a value of {nameof(EPhaseOffset)}");
    }

    public override void Write(Utf8JsonWriter writer, EPhaseOffset? value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(value?.ToString());
    }
}

public class DifficultyColorConverter : JsonConverter<DifficultyColor?>
{
    public override DifficultyColor? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? enumString = reader.GetString();
        if (enumString == null)
        {
            return null;
        }
        else if (Enum.TryParse(enumString, out DifficultyColor enumValue))
        {
            return enumValue;
        }
        throw new JsonException($"Unable to parse '{enumString}' as a value of {nameof(DifficultyColor)}");
    }

    public override void Write(Utf8JsonWriter writer, DifficultyColor? value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(value?.ToString());
    }
}

public class LightmapQualityConverter : JsonConverter<LightmapQuality?>
{
    public override LightmapQuality? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        string? enumString = reader.GetString();
        if (enumString == null)
        {
            return null;
        }
        else if (Enum.TryParse(enumString, out LightmapQuality enumValue))
        {
            return enumValue;
        }
        throw new JsonException($"Unable to parse '{enumString}' as a value of {nameof(LightmapQuality)}");
    }

    public override void Write(Utf8JsonWriter writer, LightmapQuality? value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(value?.ToString());
    }
}
/// <summary>Reads a Vec2 from a JSON array [x, y].</summary>
public class Vec2ArrayConverter : JsonConverter<Vec2>
{
    public override Vec2 Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var values = JsonSerializer.Deserialize<float[]>(ref reader, options);
        if (values is null || values.Length != 2)
            throw new JsonException("Vec2 must be an array of 2 numbers.");
        return new Vec2(values[0], values[1]);
    }

    public override void Write(Utf8JsonWriter writer, Vec2 value, JsonSerializerOptions options)
    {
        writer.WriteStartArray();
        writer.WriteNumberValue(value.X);
        writer.WriteNumberValue(value.Y);
        writer.WriteEndArray();
    }
}

/// <summary>Reads a System.Drawing.Color from a JSON array [r, g, b] or [r, g, b, a], components 0..1.</summary>
public class ColorArrayConverter : JsonConverter<System.Drawing.Color>
{
    static int ToByte(float v) => (int)Math.Round(Math.Clamp(v, 0f, 1f) * 255f);

    public override System.Drawing.Color Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var v = JsonSerializer.Deserialize<float[]>(ref reader, options);
        if (v is null || (v.Length != 3 && v.Length != 4))
            throw new JsonException("Color must be an array of 3 or 4 numbers (0..1).");
        return System.Drawing.Color.FromArgb(v.Length == 4 ? ToByte(v[3]) : 255, ToByte(v[0]), ToByte(v[1]), ToByte(v[2]));
    }

    public override void Write(Utf8JsonWriter writer, System.Drawing.Color value, JsonSerializerOptions options)
    {
        writer.WriteStartArray();
        writer.WriteNumberValue(value.R / 255f);
        writer.WriteNumberValue(value.G / 255f);
        writer.WriteNumberValue(value.B / 255f);
        writer.WriteNumberValue(value.A / 255f);
        writer.WriteEndArray();
    }
}
