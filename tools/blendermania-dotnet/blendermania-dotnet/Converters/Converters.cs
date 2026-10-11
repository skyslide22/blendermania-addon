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