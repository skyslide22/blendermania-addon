using System.Text.Json;

namespace blendermania_dotnet;

public static class Constants
{
    public static JsonSerializerOptions CommonJsonSerializerOptions { get; } = new()
    {
        PropertyNameCaseInsensitive = true
    };

}