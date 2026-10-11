// using GBX.NET;
// using GBX.NET.Engines.GameData;

// namespace blendermania_dotnet
// {
//     class ConvertItemToObj
//     {
//         public string ItemPath { get; set; } = "";
//         public string OutputDir { get; set; } = "";

//         public string Exec()
//         {
//             if (ItemPath.Length == 0 || OutputDir.Length == 0)
//             {
//                 throw new Exception("ItemPath or OutputDir is empty");
//             }

//             CGameItemModel item;
//             try
//             {
//                 item = Gbx.ParseNode<CGameItemModel>(ItemPath);
//             }
//             catch
//             {
//                 throw new Exception("This type of item can not be converted");
//             }

//             if (item is null)
//             {
//                 throw new Exception("Could not parse item");
//             }

//             if (item.ItemModel is null)
//             {
//                 throw new Exception("No item geometry in the file or unsuported item type");
//             }

//             string OutputFile = Path.Join(OutputDir, $"{Path.GetFileNameWithoutExtension(ItemPath)}.obj");
//             using (FileStream fs = File.Create(OutputFile))
//             {
//                 item.ItemModel.MeshCrystal.ExportToObj(fs, new MemoryStream(), leaveOpen: false);
//             }

//             /*
//             using var objWriterStream = new MemoryStream();

//             item.ItemModel.MeshCrystal.ExportToObj(objWriterStream, new MemoryStream());

//             MemoryStream objStream = new MemoryStream(objWriterStream.ToArray());

//             objStream.Seek(0, SeekOrigin.Begin);

//             if (objStream.Length == 0)
//             {
//                 throw new Exception("Could not extract item geometry");
//             }


//             Directory.CreateDirectory(OutputDir);
//             string OutputFile = Path.Join(OutputDir, $"{Path.GetFileNameWithoutExtension(ItemPath)}.obj");

//             File.WriteAllBytes(OutputFile, objStream.ToArray());
//             */

//             return OutputFile;
//         }
//     }
// }