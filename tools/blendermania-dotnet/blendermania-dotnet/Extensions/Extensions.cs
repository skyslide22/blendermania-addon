namespace blendermania_dotnet;

public static class Extensions
{
    public static GBX.NET.Color[,] ConvertToGBXColor(this System.Drawing.Color[,] colors)
    {
        var width = colors.GetLength(0);
        var height = colors.GetLength(1);
        var result = new GBX.NET.Color[width, height];

        for (int i = 0; i < width; i++)
        {
            for (int j = 0; j < height; j++)
            {
                var color = colors[i, j];
                result[i, j] = new GBX.NET.Color(color.R / 255f, color.G / 255f, color.B / 255f, color.A / 255f);
            }
        }

        return result;
    }
}